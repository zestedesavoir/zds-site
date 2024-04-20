from datetime import datetime
import logging
import re
import time

from django.apps import apps
from django.conf import settings
from django.db import transaction

from bs4 import BeautifulSoup
from typesense import Client as TypesenseClient

from zds.searchv2.models import AbstractSearchIndexableModel


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


def get_all_indexable_classes(only_models=False):
    """Return all indexable classes"""

    classes = [model for model in apps.get_models() if issubclass(model, AbstractSearchIndexableModel)]
    if not only_models:
        # Import here instead of at the top of the file to avoid circular dependencies
        from zds.tutorialv2.models.database import FakeChapter

        classes.append(FakeChapter)
    return classes


class SearchIndexManager:
    """Manage interactions with the search engine"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.engine = None
        self.connected = False

        if settings.SEARCH_ENABLED:
            self.engine = TypesenseClient(settings.SEARCH_CONNECTION)

            try:
                self.engine.api_call.get("/health")
                self.connected = True
            except:
                self.logger.warn("failed to connect to the search engine")

    @property
    def collections(self):
        if not self.connected:
            return []

        return [c["name"] for c in self.engine.collections.retrieve()]

    def clear_index(self):
        """Remove all data and schemes from search engine and mark all objects as to be reindexed"""

        if not self.connected:
            return

        for collection in self.collections:
            self.engine.collections[collection].delete()

        for model in get_all_indexable_classes(only_models=True):
            assert issubclass(model, AbstractSearchIndexableModel)
            objs = model.get_indexable_objects(force_reindexing=True)
            objs.update(search_engine_requires_index=True)

    def reset_index(self):
        """Delete old collections and create new ones.
        Then, set schemas for the different models.

        :param models: list of models
        :type models: list
        """

        if not self.connected:
            return

        self.clear_index()
        for model in get_all_indexable_classes():
            self.engine.collections.create(model.get_document_schema())

    def indexing_of_model(self, model, force_reindexing=False, verbose=True):
        """Index documents of a given model in batch, using the ``objects_per_batch`` property.

        See https://typesense.org/docs/0.23.1/api/documents.html#index-multiple-documents

        .. attention::
            + Designed to work only with ``AbstractSearchIndexableModel``.

        :param model: a model
        :type model: AbstractSearchIndexableModel
        :param force_reindexing: force all document to be indexed
        :type force_reindexing: bool
        :param verbose: whether to display or not the progress
        :type verbose: bool
        :return: the number of indexed documents
        :rtype: int
        """

        if not self.connected:
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

                    answer = self.engine.collections[doc_type].documents.import_(
                        [obj.get_document_source() for obj in objects], {"action": "create"}
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
                        model_to_update.objects.filter(pk__in=pks).update(search_engine_requires_index=False)
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

                    answer = self.engine.collections[doc_type].documents.import_(
                        [obj.get_document_source() for obj in objects], {"action": "create"}
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
                        model.objects.filter(pk__in=[o.pk for o in objects]).update(search_engine_requires_index=False)
                        indexed_counter += len(objects)

                    # basic estimation of indexed objects per second
                    now = time.time()
                    last_batch_duration = int(now - then) or 1
                    then = now
                    obj_per_sec = round(float(objects_per_batch) / last_batch_duration, 2)
                    if force_reindexing and verbose:
                        print(f"    {indexed_counter} so far ({obj_per_sec} obj/s, batch size: {objects_per_batch})")

                    if prev_obj_per_sec is False:
                        prev_obj_per_sec = obj_per_sec
                    else:
                        ratio = obj_per_sec / prev_obj_per_sec
                        # if we processed this batch 10% slower/faster than the previous one,
                        # shrink/increase batch size
                        if abs(1 - ratio) > 0.1:
                            objects_per_batch = int(objects_per_batch * ratio)
                            if force_reindexing and verbose:
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

        if not self.connected:
            return

        doc_type = document.get_document_type()
        doc_id = document.search_engine_id
        answer = self.engine.collections[doc_type].documents[doc_id].update(fields_values)
        if not fields_values.items() <= answer.items():  # the expected answer returns the whole updated document
            self.logger.warn(f"Error when updating: {answer}.")

    def delete_document(self, document):
        """Delete a given document

        :param document: the document to delete
        :type document: AbstractSearchIndexable
        """

        if not self.connected:
            return

        doc_type = document.get_document_type()
        doc_id = document.search_engine_id
        answer = self.engine.collections[doc_type].documents[doc_id].delete()
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

        if not self.connected:
            return

        self.engine.collections[doc_type].documents.delete(query)

    def search(self, request):
        """Do a search in all collections (only used in tests)
        :param request: a string, the search request
        :type request: string
        :return: formated search
        """
        if not self.connected:
            return

        search_requests = {"searches": []}
        for collection in self.collections:
            search_requests["searches"].append({"collection": collection, "q": request})

        return self.engine.multi_search.perform(search_requests, None)["results"]


class SearchFilter:
    """Class to generate filters for Typesense queries.

    See https://typesense.org/docs/26.0/api/search.html#filter-parameters
    """

    def __init__(self):
        self.filter = ""

    def __str__(self):
        return self.filter

    def _add_filter(self, f):
        if self.filter != "":
            self.filter += " && "
        self.filter += f"({f})"

    def add_exact_filter(self, field: str, values: list):
        """
        Filter documents such as field has one of the values.

        :param field: Name of the field to apply the filter on.
        :type field: str
        :param values: A list of values the field can have.
        :type values: list
        """
        self._add_filter(f"{field}:=[" + ",".join(map(str, values)) + "]")

    def add_bool_filter(self, field: str, value: bool):
        self._add_filter(f"{field}:{str(value).lower()}")

    def add_not_numerical_filter(self, field: str, values: list[int]):
        """
        Filter documents such as field has *not* one of the values.

        :param field: Name of the field to filter.
        :type field: str
        :param values: A list of integer values the field cannot have.
        :type values: list[int]
        """
        self._add_filter(f"{field}:!=[" + ",".join(map(str, values)) + "]")
