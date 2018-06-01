from django.conf.urls import url
from zds.searchv2.views import SearchView, opensearch, SimilarTopicsView


urlpatterns = [
    url(r'^$', SearchView.as_view(), name='query'),
    url(r'^sujets-similaires/$', SimilarTopicsView.as_view(), name='similar'),
    url(r'^opensearch\.xml$', opensearch, name='opensearch'),
]
