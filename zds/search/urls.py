# coding: utf-8

from django.conf.urls import url

from zds.search.views import CustomSearchView


urlpatterns = [
    url(r'^$', CustomSearchView.as_view(), name='haystack_search'),
    url(r'^opensearch\.xml$', 'zds.search.views.opensearch', name='search-opensearch'),
]
