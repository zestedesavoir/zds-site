# coding: utf-8

from django.conf.urls import patterns, url
from haystack.views import search_view_factory

from zds.search.form import CustomSearchForm
from zds.search.views import CustomSearchView

urlpatterns = patterns('haystack.views', url(r'^$', CustomSearchView.as_view(), name='haystack_search'))

urlpatterns += patterns('',
                        url(r'^opensearch\.xml$', 'zds.search.views.opensearch')
                        )
