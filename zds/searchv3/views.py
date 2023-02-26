from zds import json_handler
import operator

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, MultiMatch, FunctionScore, Term, Terms, Range

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.detail import SingleObjectMixin

from zds.searchv3.forms import SearchForm
from zds.searchv3.models import ESIndexManager
from zds.utils.paginator import ZdSPagingListView
from zds.utils.templatetags.authorized_forums import get_authorized_forums
from functools import reduce

from .client import client


class SimilarTopicsView(CreateView, SingleObjectMixin):
    search_query = None
    authorized_forums = ""
    index_manager = None

    def __init__(self, **kwargs):
        """Overridden because the index manager must NOT be initialized elsewhere."""

        super().__init__(**kwargs)
        self.index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def get(self, request, *args, **kwargs):
        if "q" in request.GET:
            self.search_query = "".join(request.GET["q"])

        results = []
        if self.index_manager.connected_to_es and self.search_query:
            self.authorized_forums = get_authorized_forums(self.request.user)

            search_queryset = Search()
            query = (
                Match(_type="topic")
                & Terms(forum_pk=self.authorized_forums)
                & MultiMatch(query=self.search_query, fields=["title", "subtitle", "tags"])
            )

            functions_score = [
                {"filter": Match(is_solved=True), "weight": settings.ZDS_APP["search"]["boosts"]["topic"]["if_solved"]},
                {"filter": Match(is_sticky=True), "weight": settings.ZDS_APP["search"]["boosts"]["topic"]["if_sticky"]},
                {"filter": Match(is_locked=True), "weight": settings.ZDS_APP["search"]["boosts"]["topic"]["if_locked"]},
            ]

            scored_query = FunctionScore(query=query, boost_mode="multiply", functions=functions_score)
            search_queryset = search_queryset.query(scored_query)[:10]

            # Build the result
            for hit in search_queryset.execute():
                result = {
                    "id": hit.pk,
                    "url": str(hit.get_absolute_url),
                    "title": str(hit.title),
                    "subtitle": str(hit.subtitle),
                    "forumTitle": str(hit.forum_title),
                    "forumUrl": str(hit.forum_get_absolute_url),
                    "pubdate": str(hit.pubdate),
                }
                results.append(result)

        data = {"results": results}
        return HttpResponse(json_handler.dumps(data), content_type="application/json")


class SuggestionContentView(CreateView, SingleObjectMixin):
    search_query = None
    authorized_forums = ""
    index_manager = None

    def __init__(self, **kwargs):
        """Overridden because the index manager must NOT be initialized elsewhere."""

        super().__init__(**kwargs)
        self.index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def get(self, request, *args, **kwargs):
        if "q" in request.GET:
            self.search_query = "".join(request.GET["q"])
        excluded_content_ids = request.GET.get("excluded", "").split(",")
        results = []
        if self.index_manager.connected_to_es and self.search_query:
            self.authorized_forums = get_authorized_forums(self.request.user)

            search_queryset = Search()
            if len(excluded_content_ids) > 0 and excluded_content_ids != [""]:
                search_queryset = search_queryset.exclude("terms", content_pk=excluded_content_ids)
            query = Match(_type="publishedcontent") & MultiMatch(
                query=self.search_query, fields=["title", "description"]
            )

            functions_score = [
                {
                    "filter": Match(content_type="TUTORIAL"),
                    "weight": settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_tutorial"],
                },
                {
                    "filter": Match(content_type="ARTICLE"),
                    "weight": settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_article"],
                },
                {
                    "filter": Match(content_type="OPINION"),
                    "weight": settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion"],
                },
            ]

            scored_query = FunctionScore(query=query, boost_mode="multiply", functions=functions_score)
            search_queryset = search_queryset.query(scored_query)[:10]

            # Build the result
            for hit in search_queryset.execute():
                result = {
                    "id": hit.content_pk,
                    "pubdate": hit.publication_date,
                    "title": str(hit.title),
                    "description": str(hit.description),
                }
                results.append(result)

        data = {"results": results}

        return HttpResponse(json_handler.dumps(data), content_type="application/json")


class SearchView(ZdSPagingListView):
    """Search view."""

    template_name = "searchv3/search.html"
    paginate_by = settings.ZDS_APP["search"]["results_per_page"]

    search_form_class = SearchForm
    search_form = None
    search_query = None
    content_category = None
    content_subcategory = None

    authorized_forums = ""

    index_manager = None

    def __init__(self, **kwargs):
        """Overridden because the index manager must NOT be initialized elsewhere."""

        super().__init__(**kwargs)
        self.index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def get(self, request, *args, **kwargs):
        """Overridden to catch the request and fill the form."""

        if "q" in request.GET:
            self.search_query = "".join(request.GET["q"])

        self.search_form = self.search_form_class(data=self.request.GET)

        if self.search_query and not self.search_form.is_valid():
            raise PermissionDenied("research form is invalid")

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if not self.index_manager.connected_to_es:
            messages.warning(self.request, _("Impossible de se connecter à Elasticsearch"))
            return []

        if self.search_query:
            # Restrict (sub)category if any
            if self.search_form.cleaned_data["category"]:
                self.content_category = self.search_form.cleaned_data["category"]
            if self.search_form.cleaned_data["subcategory"]:
                self.content_subcategory = self.search_form.cleaned_data["subcategory"]

            # Mark that contents must come from library if required
            self.from_library = False
            if self.search_form.cleaned_data["from_library"] == "on":
                self.from_library = True
            # test typesense
            return self.get_queryset_publishedcontents()

        return []

    def get_queryset_publishedcontents(self):
        """Search in PublishedContent objects."""
        filter = ""
        if self.from_library:
            filter = self._add_a_filter("content_type", "[`TUTORIAL`, `ARTICLE`]", filter)
            # filter += "content_type == [`TUTORIAL`, `ARTICLE`]"

        if self.content_category:
            filter = self._add_a_filter("categories", self.content_category, filter)
            # filter += f"categories == {self.content_category}"

        if self.content_subcategory:
            filter = self._add_a_filter("subcategories", self.content_subcategory, filter)
            # filter += f"subcategories == {self.content_subcategory}"

        search_parameters = {
            "q": self.search_query,
            "query_by": "title,description,categories,subcategories, tags, text",
            "filter": filter,
        }

        result = client.collections["publishedcontent"].documents.search(search_parameters)

        return result["hits"]

    def get_queryset_chapters(self):
        """Search in content chapters."""

        if self.content_category:
            filter = self._add_a_filter("categories", self.content_category, filter)

        if self.content_subcategory:
            filter = self._add_a_filter("subcategories", self.content_subcategory, filter)

        search_parameters = {
            "q": self.search_query,
            "query_by": "title,text",
            "filter": filter,
        }

        result = client.collections["chapter"].documents.search(search_parameters)

        return result["hits"]

    def get_queryset_topics(self):
        """Search in topics, and remove the result if the forum is not allowed for the user.

        Score is modified if:

        + topic is solved;
        + topic is sticky;
        + topic is locked.
        """

        filter = ""
        filter = self._add_a_filter("forum_pk", self.authorized_forums, filter)
        search_parameters = {
            "q": self.search_query,
            "query_by": "title,subtitile,tags",
            "filter": filter,
        }

        result = client.collections["topic"].documents.search(search_parameters)

        return result["hits"]

    def get_queryset_posts(self):
        """Search in posts, and remove result if the forum is not allowed for the user or if the message is invisible.

        Score is modified if:

        + post is the first one in a topic;
        + post is marked as "useful";
        + post has a like/dislike ratio above (has more likes than dislikes) or below (the other way around) 1.0.
        """

        query = (
            Match(_type="post")
            & Terms(forum_pk=self.authorized_forums)
            & Term(is_visible=True)
            & MultiMatch(query=self.search_query, fields=["text_html"])
        )

        functions_score = [
            {"filter": Match(position=1), "weight": settings.ZDS_APP["search"]["boosts"]["post"]["if_first"]},
            {"filter": Match(is_useful=True), "weight": settings.ZDS_APP["search"]["boosts"]["post"]["if_useful"]},
            {
                "filter": Range(like_dislike_ratio={"gt": 1}),
                "weight": settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_above_1"],
            },
            {
                "filter": Range(like_dislike_ratio={"lt": 1}),
                "weight": settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_below_1"],
            },
        ]

        filter = ""
        filter = self._add_a_filter("forum_pk", self.authorized_forums, filter)
        filter = self._add_a_filter("is_visible", True, filter)
        search_parameters = {
            "q": self.search_query,
            "query_by": "text_html",
            "filter": filter,
        }

        result = client.collections["post"].documents.search(search_parameters)

        return result["hits"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.search_form
        context["query"] = self.search_query is not None
        print("context")
        print(context)
        return context

    def _add_a_filter(field, value, current_filter):
        """
        field : it's a string with the name of the field to filter
        value : is the a string with value of the field
        current_filter : is the current string which represent the value to filter
        """
        if len(field) > 0:
            current_filter += f"&& {field} == {str(value)}"
        else:
            current_filter = f"{field} == {str(value)}"
        return current_filter


def opensearch(request):
    """Generate OpenSearch Description file."""

    return render(
        request,
        "searchv3/opensearch.xml",
        {
            "site_name": settings.ZDS_APP["site"]["literal_name"],
            "site_url": settings.ZDS_APP["site"]["url"],
            "email_contact": settings.ZDS_APP["site"]["email_contact"],
            "language": settings.LANGUAGE_CODE,
            "search_url": settings.ZDS_APP["site"]["url"] + reverse("search:query"),
        },
        content_type="application/opensearchdescription+xml",
    )