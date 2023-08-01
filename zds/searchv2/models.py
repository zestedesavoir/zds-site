from datetime import datetime
from functools import partial
import logging
import re
import time

from django.apps import apps
from django.conf import settings
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from bs4 import BeautifulSoup
from typesense import Client as SearchEngineClient


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

    You also need to maintain ``search_engine_id`` and
    ``search_engine_already_indexed`` for indexing (if any).
    """

    search_engine_already_indexed = False
    search_engine_id = ""

    objects_per_batch = 100

    @classmethod
    def get_document_type(cls):
        """Name of the collection in the search engine for the class."""
        return cls.__name__.lower()

    @classmethod
    def get_document_schema(self):
        """Setup schema for the model (data scheme).

        See https://typesense.org/docs/0.23.1/api/collections.html#with-pre-defined-schema

        .. attention::
            You *may* want to override this method (otherwise the search engine
            choose the schema by itself).

        :return: schema object. A dictionary containing the name and fields of the collection.
        :rtype: dict
        """
        search_engine_schema = dict()
        search_engine_schema["name"] = self.get_document_type()
        search_engine_schema["fields"] = [{"name": ".*", "type": "auto"}]
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

    def get_document_source(self, excluded_fields=None):
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
        schema = cls.get_document_schema()["fields"]
        fields = list(schema[i]["name"] for i in range(len(schema)))

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

    def get_document_for_indexing(self):
        """Create a document formatted for indexing.

        See https://typesense.org/docs/0.24.1/api/documents.html#index-a-document

        :return: the document
        :rtype: dict
        """

        document = self.get_document_source()
        document["id"] = self.search_engine_id

        return document


class AbstractSearchIndexableModel(AbstractSearchIndexable, models.Model):
    """Version of AbstractSearchIndexable for a Django object, with some improvements:

    - Already include ``pk`` in schema;
    - Makes the search engine ID field to be equal to the database primary key;
    - Override ``search_engine_already_indexed`` class attribute to be a database field;
    - Define a ``search_engine_flagged`` database field to be able to index only new and modified data;
    - Override ``save()`` to mark the object as requiring to be indexed;
    - Define a ``get_indexable_objects()`` method that can be overridden to
      change the queryset to fetch objects to index.
    """

    class Meta:
        abstract = True

    search_engine_flagged = models.BooleanField(
        _("Doit être (ré)indexé par le moteur de recherche"), default=True, db_index=True
    )
    search_engine_already_indexed = models.BooleanField(
        _("Déjà indexé par le moteur de recherche"), default=False, db_index=True
    )

    def __init__(self, *args, **kwargs):
        """Override to make the search engine document ID equal to the database primary key."""
        super().__init__(*args, **kwargs)
        self.search_engine_id = str(self.pk)

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
            query = query.filter(search_engine_flagged=True)

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
        (since a save assumes a modification of the object).

        .. note::
            Flagging can be prevented using ``save(search_engine_flagged=False)``.
        """

        self.search_flagged = kwargs.pop("search_engine_flagged", True)

        return super().save(*args, **kwargs)


def date_to_timestamp_int(date):
    """Converts a given datetime object to Unix timestamp.
    The purpose of this function is for indexing datetime objects in Typesense.

    :param date: the datetime object to be converted
    :type date: datetime.datetime

    :return: the Unix timestamp corresponding to the given datetime object
    :rtype: int
    """
    return int(datetime.timestamp(date))


def clean_html(text):
    """Removes all HTML tags from the given text using BeautifulSoup.

    :param text: the text to be cleaned
    :type text: str

    :return: the cleaned text with all HTML tags removed
    :rtype: str
    """
    result = ""
    if text != None:
        soup = BeautifulSoup(text, "html.parser")
        formatted_html = soup.prettify()
        result = re.sub(r"<[^>]*>", "", formatted_html).strip()
    return result


def delete_document_in_search_engine(instance):
    """Delete an AbstractSearchIndexable from the search engine database.

    All classes that derive from AbstractSearchIndexableModel have to implement
    a ``delete_document()`` method.

    :param instance: the document to delete
    :type instance: AbstractSearchIndexable
    """

    search_engine_manager = SearchIndexManager()
    search_engine_manager.delete_document(instance)


def get_all_indexable_objects():
    """Return all indexable objects registered in Django"""
    return [model for model in apps.get_models() if issubclass(model, AbstractSearchIndexableModel)]


class SearchIndexManager:
    """Manage interactions with the search engine"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.search_engine = None
        self.connected_to_search_engine = False

        if settings.SEARCH_ENABLED:
            self.search_engine = SearchEngineClient(settings.SEARCH_CONNECTION)
            self.connected_to_search_engine = True

            # test connection:
            try:
                self.search_engine.api_call.get("/health")
            except:
                self.connected_to_search_engine = False
                self.logger.warn("failed to connect to the search engine")
            else:
                self.logger.info("connected to the search engine")

    def clear_index(self):
        """Clear index"""

        if not self.connected_to_search_engine:
            return

        collections = self.search_engine.collections.retrieve()
        for collection in collections:
            self.search_engine.collections[collection["name"]].delete()

        self.logger.info(f"index cleared, {len(collections)} collections deleted")

    def reset_index(self, models):
        """Delete old collections and create new ones.
        Then, set schemas for the different models.

        :param models: list of models
        :type models: list
        """

        if not self.connected_to_search_engine:
            return

        self.clear_index()
        models = set(models)  # avoid duplicates
        for model in models:
            schema = model.get_document_schema()
            self.search_engine.collections.create(schema)

        self.logger.info("index created")

    def clear_indexing_of_model(self, model):
        """Nullify the indexing of a given model by setting
        ``search_engine_already_index=False`` to all objects.

        :param model: the model
        :type model: class
        """

        if issubclass(model, AbstractSearchIndexableModel):  # use a global update with Django
            objs = model.get_indexable_objects(force_reindexing=True)
            objs.update(search_engine_flagged=True, search_engine_already_indexed=False)

            self.logger.info(f"unindex {model.get_document_type()}")
        elif len(model.get_indexable(force_reindexing=True)) > 0:
            # This sould never happen: if the origin object is not in the
            # database, there is no field to update and save.
            self.logger.warn(f"Did not reset indexing of {model.get_document_type()} objects")

    def indexing_of_model(self, model, force_reindexing=False):
        """Index documents of a given model. Use the ``objects_per_batch`` property to index.

        See https://typesense.org/docs/0.23.1/api/documents.html#index-multiple-documents

        .. attention::
            + Currently only working with ``AbstractSearchIndexableModel``.

        :param model: a model
        :type model: AbstractSearchIndexableModel
        :param force_reindexing: force all document to be indexed
        :type force_reindexing: bool
        :return: the number of indexed documents
        :rtype: int
        """

        if not self.connected_to_search_engine:
            return

        if not issubclass(model, AbstractSearchIndexableModel):
            return

        objects_per_batch = getattr(model, "objects_per_batch", 100)
        indexed_counter = 0
        if model.__name__ == "PublishedContent":
            generate = model.get_indexable(force_reindexing)
            while True:
                with transaction.atomic():
                    try:
                        # fetch a batch (batch management is done in PublishedContent.get_indexable()):
                        objects = next(generate)
                    except StopIteration:
                        break

                    if not objects:
                        break

                    if hasattr(objects[0], "parent_id"):
                        model_to_update = objects[0].parent_model
                        pks = [o.parent_id for o in objects]
                        doc_type = "chapter"
                    else:
                        model_to_update = model
                        pks = [o.pk for o in objects]
                        doc_type = model.get_document_type()

                    answer = self.search_engine.collections[doc_type].documents.import_(
                        [obj.get_document_for_indexing() for obj in objects], {"action": "create"}
                    )

                    error = None
                    for a in answer:
                        if "success" not in a or a["success"] is not True:
                            error = a
                            break

                    if error is not None:
                        self.logger.warn(f"Error when indexing {doc_type} objects: {error}.")
                    else:
                        # mark all these objects as indexed at once
                        model_to_update.objects.filter(pk__in=pks).update(
                            search_engine_already_indexed=True, search_engine_flagged=False
                        )
                        indexed_counter += len(objects)
        else:
            then = time.time()
            prev_obj_per_sec = False
            last_pk = 0
            object_source = model.get_indexable(force_reindexing)
            doc_type = model.get_document_type()

            while True:
                with transaction.atomic():
                    # fetch a batch
                    objects = list(object_source.filter(pk__gt=last_pk)[:objects_per_batch])

                    if not objects:
                        break

                    answer = self.search_engine.collections[doc_type].documents.import_(
                        [obj.get_document_for_indexing() for obj in objects], {"action": "create"}
                    )

                    error = None
                    for a in answer:
                        if "success" not in a or a["success"] is not True:
                            error = a
                            break

                    if error is not None:
                        self.logger.warn(f"Error when indexing {doc_type} objects: {error}.")
                    else:
                        # mark all these objects as indexed at once
                        model.objects.filter(pk__in=[o.pk for o in objects]).update(
                            search_engine_already_indexed=True, search_engine_flagged=False
                        )
                        indexed_counter += len(objects)

                    # basic estimation of indexed objects per second
                    now = time.time()
                    last_batch_duration = int(now - then) or 1
                    then = now
                    obj_per_sec = round(float(objects_per_batch) / last_batch_duration, 2)
                    if force_reindexing:
                        print(f"    {indexed_counter} so far ({obj_per_sec} obj/s, batch size: {objects_per_batch})")

                    if prev_obj_per_sec is False:
                        prev_obj_per_sec = obj_per_sec
                    else:
                        ratio = obj_per_sec / prev_obj_per_sec
                        # if we processed this batch 10% slower/faster than the previous one,
                        # shrink/increase batch size
                        if abs(1 - ratio) > 0.1:
                            objects_per_batch = int(objects_per_batch * ratio)
                            if force_reindexing:
                                print(f"     {round(ratio, 2)}x, new batch size: {objects_per_batch}")
                        prev_obj_per_sec = obj_per_sec

                    last_pk = objects[-1].pk

        return indexed_counter

    def update_single_document(self, document, fields_values):
        """Update given fields of a single document.

        See https://typesense.org/docs/0.23.1/api/documents.html#update-a-document

        :param document: the document to update
        :type document: AbstractSearchIndexable
        :param fields_values: fields to update
        :type fields_values: dict
        """

        if not self.connected_to_search_engine:
            return

        doc_type = document.get_document_type()
        doc_id = document.search_engine_id
        answer = self.search_engine.collections[doc_type].documents[doc_id].update(fields_values)
        if not fields_values.items() <= answer.items():  # the expected answer returns the whole updated document
            self.logger.warn(f"Error when updating: {answer}.")

    def delete_document(self, document):
        """Delete a given document

        :param document: the document to delete
        :type document: AbstractSearchIndexable
        """

        if not self.connected_to_search_engine:
            return

        doc_type = document.get_document_type()
        doc_id = document.search_engine_id
        answer = self.search_engine.collections[doc_type].documents[doc_id].delete()
        if "id" not in answer or answer["id"] != doc_id:
            self.logger.warn(f"Error when deleting: {answer}.")

    def delete_by_query(self, doc_type="", query={"filter_by": ""}):
        """Delete a bunch of documents that match a specific filter_by condition.

        See https://typesense.org/docs/0.23.1/api/documents.html#delete-by-query

        .. attention ::
            Call to this function must be done with great care!

        :param doc_type: the document type
        :type doc_type: str
        :param query: the query to match all document to be deleted
        :type query: search request with filter_by in the search parameters
        """

        if not self.connected_to_search_engine:
            return

        self.search_engine.collections[doc_type].documents.delete(query)

    def search(self, request):
        """Do a search
        :param request: a string, the search request
        :type request: string
        :return: formated search
        """
        if not self.connected_to_search_engine:
            return

        search_requests = {"searches": []}
        for collection in self.search_engine.collections.retrieve():
            search_requests["searches"].append({"collection": collection["name"], "q": request})

        return self.search_engine.multi_search.perform(search_requests, None)["results"]
