# coding: utf-8
from django.db import models

from elasticsearch_dsl import Mapping


class ESIndexableMixin(object):
    """Mixin for indexable objects.

    Define a number of different functions that can be overridden to tune the behavior of indexing into elasticsearch.

    You (may) need to override :

    - ``get_indexable()`` ;
    - ``get_mapping()`` (not mandatory, but otherwise, ES will choose the mapping by itself) ;
    - ``get_document()`` (not mandatory, but may be useful if data differ from mapping or extra stuffs need to be done).

    """

    @classmethod
    def get_es_content_type(cls):
        """value of the ``_type`` field in the index"""
        content_type = cls.__name__.lower()

        # fetch parents
        for base in cls.__bases__:
            if issubclass(base, ESIndexableMixin):
                content_type = base + '_' + content_type

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
        :rtype: elacticsearch_dsl.Mapping
        """
        m = Mapping(self.get_es_content_type())
        return m

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

    def get_es_document(self):
        """Create a document from the variable of the class, based on the mapping.

        .. attention::
            You may need to override this method if the data differ from the mapping for some reason.

        :return: document
        :rtype: dict
        """

        cls = self.__class__
        fields = list(cls.get_es_mapping().properties.properties.to_dict().keys())

        data = {}

        for field in fields:
            v = getattr(self, field, None)
            if callable(v):
                v = v()

            data[field] = v

        return data


class ESDjangoIndexableMixin(ESIndexableMixin, models.Model):
    """Version of ESIndexableMixin for a Django object, with some improvements :

    - Already include ``pk`` in mapping and document (``_id`` is set to ``pk``) ;
    - Define a ``es_flagged`` field to restrict the number of object to be indexed ;
    - Override ``save()`` to manage the field ;
    - Define a ``get_es_django_indexable()`` method that can be overridden to change the queryset to fetch object.
    """

    es_flagged = models.BooleanField('Doit être (ré)indexé par ES', default=True, db_index=True)

    @classmethod
    def get_es_mapping(cls):

        m = super(ESDjangoIndexableMixin, cls).get_es_mapping()
        m.field('pk', 'interger')
        return m

    @classmethod
    def get_es_django_indexable(cls, force_reindexing=False):
        """Method that can be overridden to filter django objects from database based on any criterion.

        :param force_reindexing: force to return all objects, even if they may be already indexed.
        :type force_reindexing: bool
        :return: query
        :rtype: django.db.models.query.QuerySet
        """

        q = cls.objects

        if not force_reindexing:
            q.filter(es_flagged=True)

        return q

    @classmethod
    def get_es_indexable(cls, force_reindexing=False):
        """Override ``get_es_indexable()`` in order to use the Django querysets.
        """

        q = cls.get_django_indexable(force_reindexing)

        return list(q.all())

    def get_es_document(self):
        """Override this method to match the ``_id`` field and the pk
        """

        data = super(ESDjangoIndexableMixin, self).get_es_document()
        data['_id'] = self.pk

        return data

    def save(self, *args, **kwargs):
        """Override the ``save()`` method to flag the object if saved
        (which assume a modification of the object, so the need of reindex).

        .. information::
            Flagging can be prevented using ``save(es_flagged=False)``.
        """

        flagged = kwargs.pop('es_flagged', True)
        if flagged and not self.es_flagged:
            self.es_flagged = True

        return super(ESDjangoIndexableMixin, self).save(*args, **kwargs)
