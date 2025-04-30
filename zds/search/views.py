import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from zds.forum.models import Post, Topic
from zds.search.forms import SearchForm
from zds.search.utils import SearchFilter, SearchIndexManager
from zds.tutorialv2.models.database import FakeChapter, PublishedContent
from zds.utils.paginator import ZdSPagingListView

logger = logging.getLogger(__name__)


class SimilarTopicsView(View):
    """
    This view allows you to suggest similar topics when creating a new topic on
    a forum. The idea is to avoid the creation of a topic on a subject already
    treated on the forum.
    """

    def get(self, request, *args, **kwargs):
        results = []

        search_engine_manager = SearchIndexManager()
        if search_engine_manager.connected:
            if "topic" in search_engine_manager.collections:
                search_query = request.GET.get("q", "")

                if search_query and "*" not in search_query:
                    max_similar_topics = settings.ZDS_APP["forum"]["max_similar_topics"]

                    search_parameters = {
                        "q": search_query,
                        "page": 1,
                        "per_page": max_similar_topics,
                    } | Topic.get_search_query(self.request.user)

                    hits = search_engine_manager.engine.collections["topic"].documents.search(search_parameters)["hits"]
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
            else:
                logger.warning("SimilarTopicView called, but there is no 'topic' collection.")

        return JsonResponse({"results": results})


class SuggestionContentView(View):
    """
    Staff members can choose at the end of a publication to suggest another
    content of the site.  When they want to add a suggestion, they write in a
    text field the name of the content to suggest, content proposals are then
    made, using the search engine through this view.
    """

    def get(self, request, *args, **kwargs):
        results = []

        search_engine_manager = SearchIndexManager()

        if search_engine_manager.connected:
            search_query = request.GET.get("q", "")

            if "publishedcontent" in search_engine_manager.collections:
                if search_query and "*" not in search_query:
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

                    hits = search_engine_manager.engine.collections["publishedcontent"].documents.search(
                        search_parameters
                    )["hits"]
                    assert len(hits) <= max_suggestion_search_results

                    for hit in hits:
                        document = hit["document"]
                        result = {
                            "id": document["content_pk"],
                            "title": str(document["title"]),
                        }
                        results.append(result)
            else:
                logger.warning("SuggestionContentView called, but there is no 'publishedcontent' collection.")

        return JsonResponse({"results": results})


class SearchView(ZdSPagingListView):
    """Search view."""

    template_name = "search/search.html"
    paginate_by = settings.ZDS_APP["search"]["results_per_page"]

    search_form = None
    search_query = None
    has_more_results = False

    def get(self, request, *args, **kwargs):
        """Overridden to catch the request and fill the form."""

        if "q" in request.GET:
            self.search_query = request.GET["q"]

        self.search_form = SearchForm(data=self.request.GET)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        result = []

        search_engine_manager = SearchIndexManager()

        if not search_engine_manager.connected:
            messages.warning(self.request, _("Impossible de se connecter au moteur de recherche"))
        elif not self.search_form.is_valid():
            # it can happen for instance if the model field doesn't match any possible search group (eg, &model=).
            messages.warning(self.request, _("Votre recherche est invalide."))
        elif self.search_query and "*" in self.search_query:
            # '*' is used as the search string to return all documents:
            # https://typesense.org/docs/0.23.1/api/search.html#query-parameters
            messages.warning(self.request, _("Les termes recherchés ne peuvent pas contenir le caractère '*'."))
        elif self.search_query:
            search_collections = self.search_form.cleaned_data["search_collections"]

            searches = {
                "publishedcontent": PublishedContent.get_search_query(),
                "chapter": FakeChapter.get_search_query(),
                "topic": Topic.get_search_query(self.request.user),
                "post": Post.get_search_query(self.request.user),
            }

            search_requests = {"searches": []}
            for collection in search_collections:
                searches[collection]["collection"] = collection
                search_requests["searches"].append(searches[collection])

            """
            Here, we reach a limitation of multicollection search of Typesense.
            We need to search in each collection, then merge the results,
            compute the final_score and finally sort according to the score.
            If we want to be able to show all results, we need to loop over the
            number of pages of search results found by Typesense, making a
            Typesense request in each iteration. Then we need to take into
            account which page of results the user requested. The simplest is
            to fetch all pages from Typesense, sort all results and then send
            the slice corresponding to the page requested by the user. However,
            this is a considerable waste of resources: fetching many data while
            we need only a small subset of it.

            For all this reasons, we choose to set a maximum of 250 results per
            collection. We still paginate the results presented to the user. If
            the user has to go the last page of the 250x#collections, it
            probably means they should refine their search query...

            Having a 1:1 relationship between pages returned by Typesense and
            pages sent to the user would probably be possible if all data we
            can search in were in only one collection.
            """

            common_search_params = {
                "q": self.search_query,
                # Indicates that the last word in the query should be treated as a prefix, and not as a whole word:
                "prefix": "false",
                "highlight_start_tag": '<mark class="highlighted">',
                "per_page": 250,  # this is the maximum
                "page": "1",
            }

            search_results = search_engine_manager.engine.multi_search.perform(search_requests, common_search_params)[
                "results"
            ]
            for i in range(len(search_results)):
                if "error" in search_results[i]:
                    logger.warning(f"Typesearch answered with an error: {search_results[i]['error']}")
                    messages.warning(
                        self.request, _(f"Le moteur de recherche a renvoyé une erreur: {search_results[i]['error']}")
                    )
                    break

                if "hits" in search_results[i]:
                    for entry in search_results[i]["hits"]:
                        if "text_match" in entry:
                            entry["collection"] = search_collections[i]
                            entry["document"]["final_score"] = entry["text_match"] * entry["document"]["weight"]
                            if len(entry["highlights"]) > 0:
                                entry["document"]["highlights"] = entry["highlights"][0]

                            if "tags" in entry["document"] and "tag_slugs" in entry["document"]:
                                assert len(entry["document"]["tags"]) == len(entry["document"]["tag_slugs"])
                                entry["document"]["tags"] = [
                                    {"title": entry["document"]["tags"][i], "slug": entry["document"]["tag_slugs"][i]}
                                    for i in range(len(entry["document"]["tags"]))
                                ]

                            result.append(entry)

                    if not self.has_more_results and search_results[i]["found"] > common_search_params["per_page"]:
                        self.has_more_results = True

            result.sort(key=lambda result: result["document"]["final_score"], reverse=True)

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.search_form
        context["has_query"] = self.search_query is not None
        context["has_more_results"] = self.has_more_results
        return context


def opensearch(request):
    """Generate OpenSearch Description file."""

    return render(
        request,
        "search/opensearch.xml",
        {
            "site_name": settings.ZDS_APP["site"]["literal_name"],
            "site_url": settings.ZDS_APP["site"]["url"],
            "email_contact": settings.ZDS_APP["site"]["email_contact"],
            "language": settings.LANGUAGE_CODE,
            "search_url": settings.ZDS_APP["site"]["url"] + reverse("search:query"),
        },
        content_type="application/opensearchdescription+xml",
    )
