# coding: utf-8

from django.conf.urls import patterns, url

from zds.news.views import NewsList

urlpatterns = patterns('',
                       # list
                       url(r'^$', NewsList.as_view(), name='news-list'),
)
