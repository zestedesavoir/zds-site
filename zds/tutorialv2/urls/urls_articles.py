# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListArticles
from zds.tutorialv2.feeds import LastArticlesFeedRSS, LastArticlesFeedATOM

urlpatterns = patterns('',
                       # Viewing
                       url(r'^flux/rss/$', LastArticlesFeedRSS(), name='feed-rss'),
                       url(r'^flux/atom/$', LastArticlesFeedATOM(), name='feed-atom'),

                       # Listing
                       url(r'^$', ListArticles.as_view(), name='list'))
