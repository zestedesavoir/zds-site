# coding: utf-8

from django.conf.urls import patterns, url

from zds.news.views import NewsList, NewsCreate

urlpatterns = patterns('',
                       url(r'^$', NewsList.as_view(), name='news-list'),
                       url(r'^creer/$', NewsCreate.as_view(), name='news-new'),
)
