# coding: utf-8

from django.conf.urls import url
from zds.searchv2.views import SearchView, opensearch


urlpatterns = [
    url(r'^$', SearchView.as_view(), name='query'),
    url(r'^opensearch\.xml$', opensearch, name='opensearch'),
]
