# coding: utf-8

from django.conf.urls import url
from zds.search2.views import SearchView, opensearch


urlpatterns = [
    url(r'^$', SearchView.as_view(), name='query'),
    url(r'^opensearch\.xml$', opensearch, name='opensearch'),
]
