# coding: utf-8

from django.conf.urls import patterns, url

from . import views
from haystack.views import search_view_factory
from zds.search.views import CustomSearchView
from zds.search.forms import CustomSearchForm

urlpatterns = patterns('haystack.views',
                          url(r'^$', search_view_factory(
                              view_class=CustomSearchView,
                              template='search/search.html',
                              form_class=CustomSearchForm
                          ), name='haystack_search'),
                        )
