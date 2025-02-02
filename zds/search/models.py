from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractSearchIndexable:
    """Mixin for indexable objects.

    Define a number of different functions that can be overridden to tune the
    behavior of indexing into the search_engine.

    You (may) need to override:

    - ``get_indexable()``;
    - ``get_schema()`` (not mandatory, but otherwise, the search engine will
      choose the schema by itself);
    - ``get_document()`` (not mandatory, but may be useful if data differ from
      schema or extra stuffs need to be done).

    You also need to maintain ``search_engine_id``, which is actually a string.
    For objects that are also stored in the database, we use the database
    primary key. We have to define it here (and not in child class
    ``AbstractSearchIndexableModel``) and we cannot rely on the `pk` field of
    models because there are objects indexed in the search engine, but not
    stored in the database.
    """

    search_engine_id = ""

    objects_per_batch = 100

    @classmethod
    def get_search_document_type(cls):
        """Name of the collection in the search engine for the class."""
        return cls.__name__.lower()

    @classmethod
    def get_search_document_schema(self):
        """Setup schema for the model (data scheme).

        See https://typesense.org/docs/0.23.1/api/collections.html#with-pre-defined-schema

        .. attention::
            You *may* want to override this method (otherwise the search engine
            choose the schema by itself).

        :return: schema object. A dictionary containing the name and fields of the collection.
        :rtype: dict
        """
        search_engine_schema = dict()
        search_engine_schema["name"] = self.get_search_document_type()
        search_engine_schema["fields"] = [{"name": ".*", "type": "auto"}]
        search_engine_schema["symbols_to_index"] = [
            "+",  # c++
            "#",  # c#
        ]
        return search_engine_schema

    @classmethod
    def get_indexable(cls, force_reindexing=False):
        """Return objects to index.

        .. attention::
            You need to override this method (otherwise nothing will be
            indexed).

        :param force_reindexing: force to return all objects, even if they may already be indexed.
        :type force_reindexing: bool
        :rtype: list
        """

        return []

    def get_document_source(self, excluded_fields=[]):
        """Create a document from the instance of the class, based on the schema.

        .. attention::
            You may need to override this method if the data differ from the
            schema for some reason.

        :param excluded_fields: exclude some field from the default method
        :type excluded_fields: list
        :return: document
        :rtype: dict
        """

        cls = self.__class__
        schema = cls.get_search_document_schema()["fields"]
        fields = list(schema[i]["name"] for i in range(len(schema)))

        data = {}

        for field in fields:
            if field in excluded_fields:
                data[field] = None
                continue

            v = getattr(self, field, None)
            if callable(v):
                v = v()

            data[field] = v

        data["id"] = self.search_engine_id

        return data


class AbstractSearchIndexableModel(AbstractSearchIndexable, models.Model):
    """Version of AbstractSearchIndexable for a Django object, with some improvements:

    - Already include ``pk`` in schema;
    - Makes the search engine ID field to be equal to the database primary key;
    - Define a ``search_engine_requires_index`` database field to be able to index only new and modified data;
    - Override ``save()`` to mark the object as requiring to be indexed;
    - Define a ``get_indexable_objects()`` method that can be overridden to
      change the queryset to fetch objects to index.
    """

    class Meta:
        abstract = True

    search_engine_requires_index = models.BooleanField(
        _("Doit être (ré)indexé par le moteur de recherche"), default=True, db_index=True
    )

    def __init__(self, *args, **kwargs):
        """Override to make the search engine document ID equal to the database primary key."""
        super().__init__(*args, **kwargs)

        # If the object doesn't exist yet in the database, the pk is None and
        # we will update the search_engine_id in the save() method.
        self.search_engine_id = str(self.pk) if self.pk else None

    @classmethod
    def get_indexable_objects(cls, force_reindexing=False):
        """Returns objects that will be indexed in the search engine.

        This method can be overridden to filter Django objects from database
        and prevent to index filtered out objects.

        :param force_reindexing: force to return all indexable objects, even those already indexed.
        :type force_reindexing: bool
        :return: query
        :rtype: django.db.models.query.QuerySet
        """

        query = cls.objects

        if not force_reindexing:
            query = query.filter(search_engine_requires_index=True)

        return query

    @classmethod
    def get_indexable(cls, force_reindexing=False):
        """Override ``get_indexable()`` in order to use the Django querysets and batch objects.

        :return: a queryset
        :rtype: django.db.models.query.QuerySet
        """

        return cls.get_indexable_objects(force_reindexing).order_by("pk").all()

    def save(self, *args, **kwargs):
        """Override the ``save()`` method to flag the object as requiring to be reindexed
        (since a save assumes a modification of the object) and set
        search_engine_id in case of creation.

        .. note::
            Flagging can be prevented using ``save(search_engine_requires_index=False)``.
        """

        self.search_engine_requires_index = kwargs.pop("search_engine_requires_index", True)

        ret = super().save(*args, **kwargs)

        # Now we are sure the object exists in databse, so we have a pk
        assert self.pk is not None
        self.search_engine_id = str(self.pk)

        return ret
