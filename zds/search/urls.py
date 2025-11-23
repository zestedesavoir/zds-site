from django.urls import path

from zds.search.views import SearchView, SimilarTopicsView, SuggestionContentView, opensearch

app_name = "search"

urlpatterns = [
    path("", SearchView.as_view(), name="query"),
    path("sujets-similaires/", SimilarTopicsView.as_view(), name="similar"),
    path("suggestion-contenu/", SuggestionContentView.as_view(), name="suggestion"),
    path("opensearch.xml", opensearch, name="opensearch"),
]
