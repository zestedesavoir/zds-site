# coding: utf-8

from django.conf.urls import url
from haystack.views import search_view_factory

from zds.search.form import CustomSearchForm
from zds.search.views import CustomSearchView, opensearch


urlpatterns = [
    url(r'^$', search_view_factory(view_class=CustomSearchView,
                                   template='search/search.html',
                                   form_class=CustomSearchForm),
        name='haystack_search'),

    url(r'^opensearch\.xml$', opensearch),
]
