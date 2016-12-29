# coding: utf-8

from django.conf.urls import url
from zds.search2.views import SearchView


urlpatterns = [
    url(r'^$', SearchView.as_view(), name='query')
]
