from datetime import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from zds import json_handler
from zds.forum.models import Topic, Post
from zds.searchv2.forms import SearchForm
from zds.searchv2.models import SearchIndexManager
from zds.searchv2.utils import SearchFilter
from zds.tutorialv2.models.database import FakeChapter, PublishedContent
from zds.utils.paginator import ZdSPagingListView

from typesense import Client as SearchEngineClient


class SimilarTopicsView(View):
    """
    This view allows you to suggest similar topics when creating a new topic on
    a forum. The idea is to avoid the creation of a topic on a subject already
    treated on the forum.
    """

    def get(self, request, *args, **kwargs):
        results = []

        if settings.SEARCH_ENABLED:
            search_engine = SearchEngineClient(settings.SEARCH_CONNECTION)
            search_engine_manager = SearchIndexManager()

            search_query = request.GET.get("q", "")

            if search_engine_manager.connected_to_search_engine and search_query and "*" not in search_query:
                max_similar_topics = settings.ZDS_APP["forum"]["max_similar_topics"]

                search_parameters = {
                    "q": search_query,
                    "page": 1,
                    "per_page": max_similar_topics,
                } | Topic.get_search_query(self.request.user)

                hits = search_engine.collections["topic"].documents.search(search_parameters)["hits"]
                assert len(hits) <= max_similar_topics

                for hit in hits:
                    document = hit["document"]
                    result = {
                        "id": document["forum_pk"],
                        "url": str(document["get_absolute_url"]),
                        "title": str(document["title"]),
                        "subtitle": str(document["subtitle"]),
                        "forumTitle": str(document["forum_title"]),
                        "forumUrl": str(document["forum_get_absolute_url"]),
                        "pubdate": str(datetime.fromtimestamp(document["pubdate"])),
                    }
                    results.append(result)

        data = {"results": results}
        return HttpResponse(json_handler.dumps(data), content_type="application/json")


class SuggestionContentView(View):
    """
    Staff members can choose at the end of a publication to suggest another
    content of the site.  When they want to add a suggestion, they write in a
    text field the name of the content to suggest, content proposals are then
    made, using the search engine through this view.
    """

    def get(self, request, *args, **kwargs):
        results = []

        if settings.SEARCH_ENABLED:
            search_engine = SearchEngineClient(settings.SEARCH_CONNECTION)
            search_engine_manager = SearchIndexManager()

            search_query = request.GET.get("q", "")

            if search_engine_manager.connected_to_search_engine and search_query and "*" not in search_query:
                max_suggestion_search_results = settings.ZDS_APP["content"]["max_suggestion_search_results"]

                search_parameters = {
                    "q": search_query,
                    "page": 1,
                    "per_page": max_suggestion_search_results,
                } | PublishedContent.get_search_query()

                # We exclude contents already picked as a suggestion:
                excluded_content_ids = request.GET.get("excluded", "")
                if excluded_content_ids:
                    filter_by = SearchFilter()
                    filter_by.add_not_numerical_filter("content_pk", excluded_content_ids.split(","))
                    search_parameters["filter_by"] = str(filter_by)

                hits = search_engine.collections["publishedcontent"].documents.search(search_parameters)["hits"]
                assert len(hits) <= max_suggestion_search_results

                for hit in hits:
                    document = hit["document"]
                    result = {
                        "id": document["content_pk"],
                        "title": str(document["title"]),
                    }
                    results.append(result)

        data = {"results": results}
        return HttpResponse(json_handler.dumps(data), content_type="application/json")


class SearchView(ZdSPagingListView):
    """Search view."""

    template_name = "searchv2/search.html"
    paginate_by = settings.ZDS_APP["search"]["results_per_page"]

    search_form_class = SearchForm
    search_form = None
    search_query = None
    content_category = None
    content_subcategory = None
    search_content_types = None
    search_content_types_count = None
    search_validated_content = None

    authorized_forums = ""

    search_engine_manager = None

    def __init__(self, **kwargs):
        """Overridden because the index manager must NOT be initialized elsewhere."""

        super().__init__(**kwargs)
        self.search_engine_manager = SearchIndexManager()

        self.search_engine = None

        if settings.SEARCH_ENABLED:
            self.search_engine = SearchEngineClient(settings.SEARCH_CONNECTION)

    def get(self, request, *args, **kwargs):
        """Overridden to catch the request and fill the form."""

        if "q" in request.GET:
            self.search_query = "".join(request.GET["q"])

        self.authorized_forums = get_authorized_forums(self.request.user)

        self.search_form = self.search_form_class(data=self.request.GET)

        if self.search_query and not self.search_form.is_valid():
            raise PermissionDenied("research form is invalid")

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        result = []

        if not self.search_engine_manager.connected_to_search_engine:
            messages.warning(self.request, _("Impossible de se connecter au moteur de recherche"))
        elif self.search_query == "*":
            # '*' is used as the search string to return all documents:
            # https://typesense.org/docs/0.23.1/api/search.html#query-parameters
            messages.warning(self.request, _("Recherche invalide"))
        elif self.search_query:
            # Restrict (sub)category if any
            if self.search_form.cleaned_data["category"]:
                self.content_category = self.search_form.cleaned_data["category"]
            if self.search_form.cleaned_data["subcategory"]:
                self.content_subcategory = self.search_form.cleaned_data["subcategory"]

            # Mark that contents must come from library if required
            self.from_library = False
            if self.search_form.cleaned_data["from_library"] == "on":
                self.from_library = True

            # Check in which collections search is performed
            search_collections = self.search_form.cleaned_data["models"]
            if len(search_collections) == 0:
                # Search in all collections
                search_collections = [c for _, v in settings.ZDS_APP["search"]["search_groups"].items() for c in v[1]]
            else:
                # Search in collections of selected models
                search_collections = [
                    c
                    for k, v in settings.ZDS_APP["search"]["search_groups"].items()
                    for c in v[1]
                    if k in search_collections
                ]

            # Check which content types are searched
            self.search_content_types = self.search_form.cleaned_data["content_types"]

            # Check if the content must be validated
            self.search_validated_content = self.search_form.cleaned_data["validated_content"]
            if self.search_validated_content:
                if "validated" in self.search_validated_content:
                    for t in ["tutorial", "article"]:
                        if t not in self.search_content_types:
                            self.search_content_types.append(t)
                if "no_validated" in self.search_validated_content and "opinion" not in self.search_content_types:
                    self.search_content_types.append("opinion")

            if self.search_content_types:
                if "publishedcontent" not in search_collections:
                    search_collections.append("publishedcontent")
                if "tutorial" in self.search_content_types and "chapter" not in search_collections:
                    search_collections.append("chapter")

            # Setup filters:
            filter_authorized_forums = SearchFilter()
            filter_authorized_forums.add_exact_filter("forum_pk", get_authorized_forums(self.request.user))
            filter_publishedcontent = SearchFilter()
            filter_chapter = SearchFilter()
            if self.content_category:
                filter_publishedcontent.add_exact_filter("categories", [self.content_category])
                filter_chapter.add_exact_filter("categories", [self.content_category])
            if self.content_subcategory:
                filter_publishedcontent.add_exact_filter("subcategories", [self.content_subcategory])
                filter_chapter.add_exact_filter("subcategories", [self.content_subcategory])
            if self.search_content_types:
                filter_publishedcontent.add_exact_filter("content_type", [self.search_content_types])

            search_requests = {"searches": []}

            searches = {
                "publishedcontent": {
                    "collection": "publishedcontent",
                    "q": self.search_query,
                    "query_by": "title,description,categories,subcategories,tags,text",
                    "query_by_weights": "{},{},{},{},{},{}".format(
                        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["title"],
                        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["description"],
                        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["categories"],
                        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["subcategories"],
                        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["tags"],
                        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["text"],
                    ),
                    "filter_by": str(filter_publishedcontent),
                },
                "chapter": {
                    "collection": "chapter",
                    "q": self.search_query,
                    "query_by": "title,text",
                    "query_by_weights": "{},{}".format(
                        settings.ZDS_APP["search"]["boosts"]["chapter"]["title"],
                        settings.ZDS_APP["search"]["boosts"]["chapter"]["text"],
                    ),
                    "filter_by": str(filter_chapter),
                },
                "topic": {
                    "collection": "topic",
                    "q": self.search_query,
                    "query_by": "title,subtitle,tags",
                    "query_by_weights": "{},{},{}".format(
                        settings.ZDS_APP["search"]["boosts"]["topic"]["title"],
                        settings.ZDS_APP["search"]["boosts"]["topic"]["subtitle"],
                        settings.ZDS_APP["search"]["boosts"]["topic"]["tags"],
                    ),
                    "filter_by": str(filter_authorized_forums),
                },
                "post": {
                    "collection": "post",
                    "q": self.search_query,
                    "query_by": "text_html",
                    "query_by_weights": "{}".format(
                        settings.ZDS_APP["search"]["boosts"]["post"]["text_html"],
                    ),
                    "filter_by": str(filter_authorized_forums),
                },
            }

            # Check if the search is in several collections or not
            if len(search_collections) == 1:
                result = self._choose_single_collection_method(search_collections[0])
            else:
                for collection in search_collections:
                    search_requests["searches"].append(searches[collection])
                result = self.get_queryset_multisearch(search_requests, search_collections)

        return result

    def get_queryset_multisearch(self, search_requests, collection_names):
        """Return search in several collections
        @search_requests : parameters of search
        @collection_names : name of the collection to search
        """
        all_collection_result = []

        common_search_params = {
            "prefix": "false",  # Indicates that the last word in the query should be treated as a prefix, and not as a whole word.
        }

        results = self.search_engine.multi_search.perform(search_requests, common_search_params)["results"]
        for k in range(len(results)):
            if "hits" in results[k]:
                for entry in results[k]["hits"]:
                    if "text_match" in entry:
                        entry["collection"] = collection_names[k]
                        entry["document"]["final_score"] = entry["text_match"] * entry["document"]["score"]
                        entry["document"]["highlights"] = entry["highlights"][0]
                        all_collection_result.append(entry)

            all_collection_result.sort(key=lambda result: result["document"]["final_score"], reverse=True)

        return all_collection_result

    def get_queryset_publishedcontents(self):
        """Search in PublishedContent collection."""
        filter_by = SearchFilter()
        if self.search_content_types:
            filter_by.add_exact_filter("content_type", self.search_content_types)

        if self.content_category:
            filter_by.add_exact_filter("categories", self.content_category)

        if self.content_subcategory:
            filter_by.add_exact_filter("subcategories", self.content_subcategory)

        search_parameters = {
            "q": self.search_query,
            "query_by": "title,description,categories,subcategories, tags, text",
            "filter_by": str(filter_by),
            "sort_by": "score:desc",
            "prefix": "false",  # Indicates that the last word in the query should be treated as a prefix, and not as a whole word.
        }

        result = self.search_engine.collections["publishedcontent"].documents.search(search_parameters)["hits"]

        for entry in result:
            entry["collection"] = "publishedcontent"
            entry["document"]["highlights"] = entry["highlights"][0]

        return result

    def get_queryset_chapters(self):
        """Search in chapters collection."""
        filter_by = SearchFilter()
        if self.content_category:
            filter_by.add_exact_filter("categories", self.content_category)

        if self.content_subcategory:
            filter_by.add_exact_filter("subcategories", self.content_subcategory)

        search_parameters = {
            "q": self.search_query,
            "query_by": "title,text",
            "filter_by": str(filter_by),
            "sort_by": "score:desc",
            "prefix": "false",  # Indicates that the last word in the query should be treated as a prefix, and not as a whole word.
        }

        result = self.search_engine.collections["chapter"].documents.search(search_parameters)["hits"]

        for entry in result:
            entry["collection"] = "chapter"
            entry["document"]["highlights"] = entry["highlights"][0]

        return result

    def get_queryset_topics(self):
        """Search in topics, and remove the result if the forum is not allowed for the user.

        Score is modified if:

        + topic is solved;
        + topic is sticky;
        + topic is locked.
        """
        filter_by = SearchFilter()
        filter_by.add_exact_filter("forum_pk", self.authorized_forums)

        search_parameters = {
            "q": self.search_query,
            "query_by": "title,subtitle,tags",
            "filter_by": str(filter_by),
            "sort_by": "score:desc",
            "prefix": "false",  # Indicates that the last word in the query should be treated as a prefix, and not as a whole word.
        }

        result = self.search_engine.collections["topic"].documents.search(search_parameters)["hits"]

        for entry in result:
            entry["collection"] = "topic"
            entry["document"]["highlights"] = entry["highlights"][0]

        return result

    def get_queryset_posts(self):
        """Search in posts, and remove result if the forum is not allowed for the user or if the message is invisible.

        Score is modified if:

        + post is the first one in a topic;
        + post is marked as "useful";
        + post has a like/dislike ratio above (has more likes than dislikes) or below (the other way around) 1.0.
        """

        filter_by = SearchFilter()
        filter_by.add_exact_filter("forum_pk", self.authorized_forums)
        filter_by.add_bool_filter("is_visible", True)
        search_parameters = {
            "q": self.search_query,
            "query_by": "text_html",
            "filter_by": str(filter_by),
            "sort_by": "score:desc",
            "prefix": "false",  # Indicates that the last word in the query should be treated as a prefix, and not as a whole word.
        }

        result = self.search_engine.collections["post"].documents.search(search_parameters)["hits"]

        for entry in result:
            entry["collection"] = "post"
            entry["document"]["highlights"] = entry["highlights"][0]

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.search_form
        context["query"] = self.search_query is not None
        return context

    def _choose_single_collection_method(self, name):
        """
        Return the result of search according the @name of the collection
        """
        if name == "publishedcontent":
            return self.get_queryset_publishedcontents()
        elif name == "post":
            return self.get_queryset_posts()
        elif name == "topic":
            return self.get_queryset_topics()
        else:
            raise "Unknown collection name"


def opensearch(request):
    """Generate OpenSearch Description file."""

    return render(
        request,
        "searchv2/opensearch.xml",
        {
            "site_name": settings.ZDS_APP["site"]["literal_name"],
            "site_url": settings.ZDS_APP["site"]["url"],
            "email_contact": settings.ZDS_APP["site"]["email_contact"],
            "language": settings.LANGUAGE_CODE,
            "search_url": settings.ZDS_APP["site"]["url"] + reverse("search:query"),
        },
        content_type="application/opensearchdescription+xml",
    )
