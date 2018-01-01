from functools import partial
import logging
import time

from django.apps import apps
from django.db import models
from django.conf import settings

from elasticsearch.helpers import parallel_bulk
from elasticsearch import ConnectionError
from elasticsearch_dsl import Mapping
from elasticsearch_dsl.query import MatchAll
from elasticsearch_dsl.connections import connections

from django.db import transaction


def es_document_mapper(force_reindexing, index, obj):
    action = 'update' if obj.es_already_indexed and not force_reindexing else 'index'
    return obj.get_es_document_as_bulk_action(index, action)


class AbstractESIndexable(object):
    """Mixin for indexable objects.

    Define a number of different functions that can be overridden to tune the behavior of indexing into elasticsearch.

    You (may) need to override :

    - ``get_indexable()`` ;
    - ``get_mapping()`` (not mandatory, but otherwise, ES will choose the mapping by itself) ;
    - ``get_document()`` (not mandatory, but may be useful if data differ from mapping or extra stuffs need to be done).

    You also need to maintain ``es_id`` and ``es_already_indexed`` for bulk indexing/updating (if any).
    """

    es_already_indexed = False
    es_id = ''

    objects_per_batch = 100

    @classmethod
    def get_es_document_type(cls):
        """value of the ``_type`` field in the index"""
        content_type = cls.__name__.lower()

        # fetch parents
        for base in cls.__bases__:
            if issubclass(base, AbstractESIndexable) and base != AbstractESDjangoIndexable:
                content_type = base.__name__.lower() + '_' + content_type

        return content_type

    @classmethod
    def get_es_mapping(self):
        """Setup mapping (data scheme).

        .. note::
            You will probably want to change the analyzer and boost value.
            Also consider the ``index='not_analyzed'`` option to improve performances.

        See https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#mappings

        .. attention::
            You *may* want to override this method (otherwise ES choose the mapping by itself).

        :return: mapping object
        :rtype: elasticsearch_dsl.Mapping
        """

        es_mapping = Mapping(self.get_es_document_type())
        return es_mapping

    @classmethod
    def get_es_indexable(cls, force_reindexing=False):
        """Return objects to index.

        .. attention::
            You need to override this method (otherwise nothing will be indexed).

        :param force_reindexing: force to return all objects, even if they may already be indexed.
        :type force_reindexing: bool
        :rtype: list
        """

        return []

    def get_es_document_source(self, excluded_fields=None):
        """Create a document from the variable of the class, based on the mapping.

        .. attention::
            You may need to override this method if the data differ from the mapping for some reason.

        :param excluded_fields: exclude some field from the default method
        :type excluded_fields: list
        :return: document
        :rtype: dict
        """

        cls = self.__class__
        fields = list(cls.get_es_mapping().properties.properties.to_dict().keys())

        data = {}

        for field in fields:
            if excluded_fields and field in excluded_fields:
                data[field] = None
                continue

            v = getattr(self, field, None)
            if callable(v):
                v = v()

            data[field] = v

        return data

    def get_es_document_as_bulk_action(self, index, action='index'):
        """Create a document formatted for a ``_bulk`` operation. Formatting is done based on action.

        See https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html.

        :param index: index in witch the document will be inserted
        :type index: str
        :param action: action, either "index", "update" or "delete"
        :type action: str
        :return: the document
        :rtype: dict
        """

        if action not in ['index', 'update', 'delete']:
            raise ValueError('action must be `index`, `update` or `delete`')

        document = {
            '_op_type': action,
            '_index': index,
            '_type': self.get_es_document_type()
        }

        if action == 'index':
            if self.es_id:
                document['_id'] = self.es_id
            document['_source'] = self.get_es_document_source()
        elif action == 'update':
            document['_id'] = self.es_id
            document['doc'] = self.get_es_document_source()
        elif action == 'delete':
            document['_id'] = self.es_id

        return document


class AbstractESDjangoIndexable(AbstractESIndexable, models.Model):
    """Version of AbstractESIndexable for a Django object, with some improvements :

    - Already include ``pk`` in mapping ;
    - Match ES ``_id`` field and ``pk`` ;
    - Override ``es_already_indexed`` to a database field.
    - Define a ``es_flagged`` field to restrict the number of object to be indexed ;
    - Override ``save()`` to manage the field ;
    - Define a ``get_es_django_indexable()`` method that can be overridden to change the queryset to fetch object.
    """

    class Meta:
        abstract = True

    es_flagged = models.BooleanField('Doit être (ré)indexé par ES', default=True, db_index=True)
    es_already_indexed = models.BooleanField('Déjà indexé par ES', default=False, db_index=True)

    def __init__(self, *args, **kwargs):
        """Override to match ES ``_id`` field and ``pk``"""
        super(AbstractESDjangoIndexable, self).__init__(*args, **kwargs)
        self.es_id = str(self.pk)

    @classmethod
    def get_es_mapping(cls):
        """Overridden to add pk into mapping.

        :return: mapping object
        :rtype: elasticsearch_dsl.Mapping
        """

        es_mapping = super(AbstractESDjangoIndexable, cls).get_es_mapping()
        es_mapping.field('pk', 'integer')
        return es_mapping

    @classmethod
    def get_es_django_indexable(cls, force_reindexing=False):
        """Method that can be overridden to filter django objects from database based on any criterion.

        :param force_reindexing: force to return all objects, even if they may be already indexed.
        :type force_reindexing: bool
        :return: query
        :rtype: django.db.models.query.QuerySet
        """

        query = cls.objects

        if not force_reindexing:
            query = query.filter(es_flagged=True)

        return query

    @classmethod
    def get_es_indexable(cls, force_reindexing=False):
        """Override ``get_es_indexable()`` in order to use the Django querysets and batch objects.

        :return: a queryset
        :rtype: django.db.models.query.QuerySet
        """

        return cls.get_es_django_indexable(force_reindexing).order_by('pk').all()

    def save(self, *args, **kwargs):
        """Override the ``save()`` method to flag the object if saved
        (which assumes a modification of the object, so the need to reindex).

        .. note::
            Flagging can be prevented using ``save(es_flagged=False)``.
        """

        self.es_flagged = kwargs.pop('es_flagged', True)

        return super(AbstractESDjangoIndexable, self).save(*args, **kwargs)


def delete_document_in_elasticsearch(instance):
    """Delete a ESDjangoIndexable from ES database.
    Must be implemented by all classes that derive from AbstractESDjangoIndexable.

    :param instance: the document to delete
    :type instance: AbstractESIndexable
    """

    index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    if index_manager.index_exists:
        index_manager.delete_document(instance)
        index_manager.refresh_index()


def get_django_indexable_objects():
    """Return all indexable objects registered in Django"""
    return [model for model in apps.get_models() if issubclass(model, AbstractESDjangoIndexable)]


class NeedIndex(Exception):
    """Raised when an action requires an index, but it is not created (yet)."""
    pass


class ESIndexManager(object):
    """Manage a given index with different taylor-made functions"""

    def __init__(self, name, shards=5, replicas=0, connection_alias='default'):
        """Create a manager for a given index

        :param name: the index name
        :type name: str
        :param shards: number of shards
        :type shards: int
        :param replicas: number of replicas
        :type replicas: int
        :param connection_alias: the alias for connection
        :type connection_alias: str
        """

        self.index = name
        self.index_exists = False

        self.number_of_shards = shards
        self.number_of_replicas = replicas

        self.logger = logging.getLogger(
            '{}.{}:{}'.format(__name__, self.__class__.__name__, self.index)
        )

        self.es = None
        self.connected_to_es = False

        if settings.ES_ENABLED:
            self.es = connections.get_connection(alias=connection_alias)
            self.connected_to_es = True

            # test connection:
            try:
                self.es.info()
            except ConnectionError:
                self.connected_to_es = False
                self.logger.warn('failed to connect to ES cluster')
            else:
                self.logger.info('connected to ES cluster')

            if self.connected_to_es:
                self.index_exists = self.es.indices.exists(self.index)

    def clear_es_index(self):
        """Clear index
        """

        if not self.connected_to_es:
            return

        if self.es.indices.exists(self.index):
            self.es.indices.delete(self.index)
            self.logger.info('index cleared')

            self.index_exists = False

    def reset_es_index(self, models):
        """Delete old index and create an new one (with the same name). Setup the number of shards and replicas.
        Then, set mappings for the different models.

        :param models: list of models
        :type models: list
        :param number_shards: number of shards
        :type number_shards: int
        :param number_replicas: number of replicas
        :type number_replicas: int
        """

        if not self.connected_to_es:
            return

        self.clear_es_index()

        mappings_def = {}

        for model in models:
            mapping = model.get_es_mapping()
            mappings_def.update(mapping.to_dict())

        self.es.indices.create(
            self.index,
            body={
                'settings': {
                    'number_of_shards': self.number_of_shards,
                    'number_of_replicas': self.number_of_replicas
                },
                'mappings': mappings_def
            }
        )

        self.index_exists = True

        self.logger.info('index created')

    def setup_custom_analyzer(self):
        """Override the default analyzer.

        See https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html.

        Our custom analyzer is based on the "french" analyzer
        (https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lang-analyzer.html#french-analyzer)
        but with some difference

        - "custom_tokenizer", to deal with punctuation and all kind of (non-breaking) spaces, but keep dashes and
          other stuffs intact (in order to keep "c++" or "c#", for example).
        - "protect_c_language", a pattern replace filter to prevent "c" from being wiped out by the stopper.
        - "french_keywords", a keyword stopper prevent some programming language from being stemmed.

        .. warning::

            You need to run ``manage.py es_manager index_all`` if you modified this !!
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        self.es.indices.close(self.index)

        document = {
            'analysis': {
                'filter': {
                    'french_elision': {
                        'type': 'elision',
                        'articles_case': True,
                        'articles': [
                            'l', 'm', 't', 'qu', 'n', 's',
                            'j', 'd', 'c', 'jusqu', 'quoiqu',
                            'lorsqu', 'puisqu'
                        ]
                    },
                    'protect_c_language': {
                        'type': 'pattern_replace',
                        'pattern': '^c$',
                        'replacement': 'langage_c'
                    },
                    'french_stop': {
                        'type': 'stop',
                        'stopwords': '_french_'
                    },
                    'french_keywords': {
                        'type': 'keyword_marker',
                        'keywords': settings.ZDS_APP['search']['mark_keywords']
                    },
                    'french_stemmer': {
                        'type': 'stemmer',
                        'language': 'light_french'
                    }
                },
                'tokenizer': {
                    'custom_tokenizer': {
                        'type': 'pattern',
                        'pattern': '[ .,!?%\u2026\u00AB\u00A0\u00BB\u202F\uFEFF\u2013\u2014\n]'
                    }
                },
                'analyzer': {
                    'default': {
                        'tokenizer': 'custom_tokenizer',
                        'filter': [
                            'lowercase',
                            'protect_c_language',
                            'french_elision',
                            'french_stop',
                            'french_keywords',
                            'french_stemmer'
                        ],
                        'char_filter': [
                            'html_strip',
                        ]
                    }
                }
            }
        }

        self.es.indices.put_settings(index=self.index, body=document)
        self.es.indices.open(self.index)

        self.logger.info('setup analyzer')

    def clear_indexing_of_model(self, model):
        """Nullify the indexing of a given model by setting ``es_already_index=False`` to all objects.

        Use full updating for ``AbstractESDjangoIndexable``, instead of saving all of them.

        :param model: the model
        :type model: class
        """

        if issubclass(model, AbstractESDjangoIndexable):  # use a global update with Django
            objs = model.get_es_django_indexable(force_reindexing=True)
            objs.update(es_flagged=True, es_already_indexed=False)
        else:
            for objects in model.get_es_indexable(force_reindexing=True):
                for obj in objects:
                    obj.es_already_indexed = False

        self.logger.info('unindex {}'.format(model.get_es_document_type()))

    def es_bulk_indexing_of_model(self, model, force_reindexing=False):
        """Perform a bulk action on documents of a given model. Use the ``objects_per_batch`` property to index.

        See http://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.bulk
        and http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.parallel_bulk

        .. attention::
            + Currently only implemented with "index" and "update" !
            + Currently only working with ``AbstractESDjangoIndexable``.

        :param model: and model
        :type model: class
        :param force_reindexing: force all document to be returned
        :type force_reindexing: bool
        :return: the number of documents indexed
        :rtype: int
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        # better safe than sorry
        if model.__name__ == 'FakeChapter':
            self.logger.warn('Cannot index FakeChapter model. Please index its parent model.')
            return 0

        documents_formatter = partial(es_document_mapper, force_reindexing, self.index)
        objects_per_batch = getattr(model, 'objects_per_batch', 100)
        indexed_counter = 0
        if model.__name__ == 'PublishedContent':
            generate = model.get_es_indexable(force_reindexing)
            while True:
                with transaction.atomic():
                    try:
                        # fetch a batch
                        objects = next(generate)
                    except StopIteration:
                        break
                    if not objects:
                        break
                    if hasattr(objects[0], 'parent_model'):
                        model_to_update = objects[0].parent_model
                        pks = [o.parent_id for o in objects]
                    else:
                        model_to_update = model
                        pks = [o.pk for o in objects]

                    formatted_documents = list(map(documents_formatter, objects))

                    for _, hit in parallel_bulk(
                        self.es,
                        formatted_documents,
                        chunk_size=objects_per_batch,
                        request_timeout=30
                    ):
                        action = list(hit.keys())[0]
                        self.logger.info('{} {} with id {}'.format(action, hit[action]['_type'], hit[action]['_id']))

                    # mark all these objects as indexed at once
                    model_to_update.objects.filter(pk__in=pks) \
                                           .update(es_already_indexed=True, es_flagged=False)
                    indexed_counter += len(objects)
            return indexed_counter
        else:
            then = time.time()
            prev_obj_per_sec = False
            last_pk = 0
            object_source = model.get_es_indexable(force_reindexing)

            while True:
                with transaction.atomic():
                    # fetch a batch
                    objects = list(object_source.filter(pk__gt=last_pk)[:objects_per_batch])
                    if not objects:
                        break

                    formatted_documents = list(map(documents_formatter, objects))

                    for _, hit in parallel_bulk(
                        self.es,
                        formatted_documents,
                        chunk_size=objects_per_batch,
                        request_timeout=30
                    ):
                        if self.logger.getEffectiveLevel() <= logging.INFO:
                            action = list(hit.keys())[0]
                            self.logger.info('{} {} with id {}'.format(
                                action, hit[action]['_type'], hit[action]['_id']))

                    # mark all these objects as indexed at once
                    model.objects.filter(pk__in=[o.pk for o in objects]) \
                                 .update(es_already_indexed=True, es_flagged=False)
                    indexed_counter += len(objects)

                    # basic estimation of indexed objects per second
                    now = time.time()
                    last_batch_duration = int(now - then) or 1
                    then = now
                    obj_per_sec = round(float(objects_per_batch) / last_batch_duration, 2)
                    if force_reindexing:
                        print('    {} so far ({} obj/s, batch size: {})'.format(
                              indexed_counter, obj_per_sec, objects_per_batch))

                    if prev_obj_per_sec is False:
                        prev_obj_per_sec = obj_per_sec
                    else:
                        ratio = obj_per_sec / prev_obj_per_sec
                        # if we processed this batch 10% slower/faster than the previous one,
                        # shrink/increase batch size
                        if abs(1 - ratio) > 0.1:
                            objects_per_batch = int(objects_per_batch * ratio)
                            if force_reindexing:
                                print('     {}x, new batch size: {}'.format(round(ratio, 2), objects_per_batch))
                        prev_obj_per_sec = obj_per_sec

                    # fetch next batch
                    last_pk = objects[-1].pk

            return indexed_counter

    def refresh_index(self):
        """Force the refreshing the index. The task is normally done periodically, but may be forced with this method.

        See https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-refresh.html.

        .. note::

            The use of this function is mandatory if you want to use the search right after an indexing.
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        self.es.indices.refresh(self.index)

    def update_single_document(self, document, doc):
        """Update given fields of a single document.

        See https://www.elastic.co/guide/en/elasticsearch/guide/current/partial-updates.html.

        :param document: the document
        :type document: AbstractESIndexable
        :param doc: fields to update
        :type doc: dict
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        arguments = {'index': self.index, 'doc_type': document.get_es_document_type(), 'id': document.es_id}
        if self.es.exists(**arguments):
            self.es.update(body={'doc': doc}, **arguments)
            self.logger.info('partial_update {} with id {}'.format(document.get_es_document_type(), document.es_id))

    def delete_document(self, document):
        """Delete a given document, based on its ``es_id``

        :param document: the document
        :type document: AbstractESIndexable
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        arguments = {'index': self.index, 'doc_type': document.get_es_document_type(), 'id': document.es_id}
        if self.es.exists(**arguments):
            self.es.delete(**arguments)
            self.logger.info('delete {} with id {}'.format(document.get_es_document_type(), document.es_id))

    def delete_by_query(self, doc_type='', query=MatchAll()):
        """Perform a deletion trough the ``_delete_by_query`` API.

        See https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-delete-by-query.html

        .. attention ::
            Call to this function must be done with great care!

        :param doc_type: the document type
        :type doc_type: str
        :param query: the query to match all document to be deleted
        :type query: elasticsearch_dsl.query.Query
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        response = self.es.delete_by_query(index=self.index, doc_type=doc_type, body={'query': query})

        self.logger.info('delete_by_query {}s ({})'.format(doc_type, response['deleted']))

    def analyze_sentence(self, request):
        """Use the anlyzer on a given sentence. Get back the list of tokens.

        See http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-analyze.html.

        This is useful to perform "terms" queries instead of full-text queries.

        :param request: a sentence from user input
        :type request: str
        :return: the tokens
        :rtype: list
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        document = {'text': request}
        tokens = []
        for token in self.es.indices.analyze(index=self.index, body=document)['tokens']:
            tokens.append(token['token'])

        return tokens

    def setup_search(self, request):
        """Setup search to the good index

        :param request: the search request
        :type request: elasticsearch_dsl.Search
        :return: formated search
        :rtype: elasticsearch_dsl.Search
        """

        if not self.connected_to_es:
            return

        if not self.index_exists:
            raise NeedIndex()

        return request.index(self.index).using(self.es)
