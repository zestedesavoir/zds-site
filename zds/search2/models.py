# coding: utf-8
from django.apps import apps
from django.db import models
from django.db.transaction import atomic
from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import Mapping
from elasticsearch_dsl.connections import connections


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

    @classmethod
    def get_es_content_type(cls):
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

        .. information::
            You will probably want to change the analyzer and boost value.
            Also consider the ``index='not_analyzed'`` option to improve performances.

        See https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#mappings

        .. attention::
            You *may* want to override this method (otherwise ES choose the mapping by itself).

        :return: mapping object
        :rtype: elasticsearch_dsl.Mapping
        """

        es_mapping = Mapping(self.get_es_content_type())
        return es_mapping

    @classmethod
    def get_es_indexable(cls, force_reindexing=False):
        """Get a list of object to be indexed. Thought this method, you may limit the reindexing.

        .. attention::
            You need to override this method (otherwise nothing will be indexed).

        :param force_reindexing: force to return all objects, even if they may be already indexed.
        :type force_reindexing: bool
        :return: list of object to be indexed
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
        """Create a document as formatted in a ``_bulk`` operation. Formatting is done based on action.

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
            '_type': self.get_es_content_type()
        }

        if action == 'index':
            if self.es_id != '':
                document['_id'] = self.es_id
            document['_source'] = self.get_es_document_source()
        if action == 'update':
            document['_id'] = self.es_id
            document['doc'] = self.get_es_document_source()
        if action == 'delete':
            document['_id'] = self.es_id

        return document

    def es_done_indexing(self, es_id):
        """Save index when indexed

        :param es_id: the id given by ES
        :type es_id: str
        """

        self.es_id = es_id
        self.es_already_indexed = True


class AbstractESDjangoIndexable(AbstractESIndexable, models.Model):
    """Version of AbstractESIndexable for a Django object, with some improvements :

    - Already include ``pk`` in mapping ;
    - Match ES ``_id`` field and ``pk`` ;
    - Overide ``es_already_indexed`` to a database field.
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
        """Override ``get_es_indexable()`` in order to use the Django querysets.
        """

        query = cls.get_es_django_indexable(force_reindexing)

        return list(query.all())

    def save(self, *args, **kwargs):
        """Override the ``save()`` method to flag the object if saved
        (which assume a modification of the object, so the need of reindex).

        .. information::
            Flagging can be prevented using ``save(es_flagged=False)``.
        """

        self.es_flagged = kwargs.pop('es_flagged', True)

        return super(AbstractESDjangoIndexable, self).save(*args, **kwargs)

    def es_done_indexing(self, es_id):
        """Overridden to actually save the values of ``es_flagged`` and ``es_already_indexed`` into BDD.

        :param es_id: id given by ES
        :type es_id: str
        :raise ValueError: if id given by ES and pk does not match.
        """

        if es_id != self.es_id:
            raise ValueError('mistmach between pk and id given by ES !!')

        super(AbstractESDjangoIndexable, self).es_done_indexing(es_id)
        self.save(es_flagged=False)


def get_django_indexable_objects():
    """Return all indexable objects registered in Django"""
    return [model for model in apps.get_models() if issubclass(model, AbstractESDjangoIndexable)]


class ESIndexManager(object):

    def __init__(self, index, connection_alias='default'):
        """Create a manager for a given index

        :param index: the index
        :type index: str
        :param connection_alias: the alias for connection
        :type connection_alias: str
        """

        self.index = index
        self.es = connections.get_connection(alias=connection_alias)

    def clear_es_index(self):
        """Clear index
        """

        if self.es.indices.exists(self.index):
            self.es.indices.delete(self.index)

    def reset_es_index(self):
        """Delete old index and create an new one (with the same name)
        """

        self.clear_es_index()
        self.es.indices.create(self.index)

    def setup_es_mappings(self, models):
        """set mapping for the different models

        :param models: list of models
        :type models: list
        """

        for model in models:
            mapping = model.get_es_mapping()
            mapping.save(self.index)

    def setup_custom_analyzer(self):
        """Override the default analyzer.

        See https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html.

        Our custom analyzer is based on the "french" analyzer
        (https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lang-analyzer.html#french-analyzer)
        but with some difference

        - "whitespace" analyzer instead of the "default" one, to keep special character intact (such as "+" like "c++")
        - "protect_c_language", a pattern replace filter to prevent "c" from being wiped out by the stopper
        - "french_keywords", a keyword stopper prevent some programming language from being stemmed
        """

        self.es.indices.close(self.index)

        document = {
            "analysis": {
                "filter": {
                    "french_elision": {
                        "type": "elision",
                        "articles_case": True,
                        "articles": [
                            "l", "m", "t", "qu", "n", "s",
                            "j", "d", "c", "jusqu", "quoiqu",
                            "lorsqu", "puisqu"
                        ]
                    },
                    "protect_c_language": {
                        "type": "pattern_replace",
                        "pattern": "^c$",
                        "replacement": "langage_c"
                    },
                    "french_stop": {
                        "type": "stop",
                        "stopwords": "_french_"
                    },
                    "french_keywords": {
                        "type": "keyword_marker",
                        "keywords": ['javafx', 'haskell', 'groovy', 'powershell']
                    },
                    "french_stemmer": {
                        "type": "stemmer",
                        "language": "light_french"
                    }
                },
                "analyzer": {
                    "default": {
                        "tokenizer": "whitespace",
                        "filter": [
                            "lowercase",
                            "protect_c_language",
                            "french_elision",
                            "french_stop",
                            "french_keywords",
                            "french_stemmer"
                        ],
                        "char_filter": [
                            "html_strip",
                        ]
                    }
                }
            }
        }

        self.es.indices.put_settings(index=self.index, body=document)
        self.es.indices.open(self.index)

    @atomic
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
            objs = list(model.get_es_indexable(force_reindexing=True))
            for obj in objs:
                obj.es_already_indexed = False

    @atomic
    def es_bulk_indexing_of_model(self, model, force_reindexing=False):
        """Perform a bulk action on documents of a given model.

        See http://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.bulk
        and http://elasticsearch-py.readthedocs.io/en/master/helpers.html#elasticsearch.helpers.streaming_bulk

        .. attention::
            Currently only implemented with "index" and "update" !

        :param model: and model
        :type model: class
        :param force_reindexing: force all document to be returned
        :type force_reindexing: bool
        """

        objs = list(model.get_es_indexable(force_reindexing=force_reindexing))
        documents = [
            obj.get_es_document_as_bulk_action(
                self.index, 'update' if obj.es_already_indexed and not force_reindexing else 'index')
            for obj in objs]

        for index, (_, hit) in enumerate(streaming_bulk(self.es, documents)):
            obj = objs[index]
            action = 'update' if obj.es_already_indexed and not force_reindexing else 'index'
            objs[index].es_done_indexing(es_id=hit[action]['_id'])
            print(hit)

    def refresh_index(self):
        """Refresh the index. The task is done periodically, but may be forced
        """

        self.es.indices.refresh(self.index)

    def analyze_sentence(self, request):
        """Use the anlyzer on a given sentence. Get back the list of tokens.

        See http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-analyze.html.

        This is useful to perform "terms" queries instead of full-text queries.

        :param request: a sentence from user input
        :type request: str
        :return: the tokens
        :rtype: list
        """

        document = {'text': request}
        tokens = []
        for token in self.es.indices.analyze(index=self.index, body=document)['tokens']:
            tokens.append(token['token'])

        return tokens
