from django.conf.urls import url

from zds.search.views import CustomSearchView, opensearch


urlpatterns = [
    url(r'^$', CustomSearchView.as_view(), name='haystack_search'),
    url(r'^opensearch\.xml$', opensearch, name='search-opensearch'),
]
