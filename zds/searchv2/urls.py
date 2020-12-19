from django.urls import re_path
from zds.searchv2.views import SearchView, opensearch, SimilarTopicsView, SuggestionContentView

urlpatterns = [
    re_path(r"^$", SearchView.as_view(), name="query"),
    re_path(r"^sujets-similaires/$", SimilarTopicsView.as_view(), name="similar"),
    re_path(r"^suggestion-contenu/$", SuggestionContentView.as_view(), name="suggestion"),
    re_path(r"^opensearch\.xml$", opensearch, name="opensearch"),
]
