# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListArticles, DisplayOnlineArticle
from zds.tutorialv2.feeds import LastArticlesFeedRSS, LastArticlesFeedATOM

urlpatterns = patterns('',
                       # Flux
                       url(r'^flux/rss/$', LastArticlesFeedRSS(), name='feed-rss'),
                       url(r'^flux/atom/$', LastArticlesFeedATOM(), name='feed-atom'),

                       # View
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayOnlineArticle.as_view(), name='view'),

                       # Listing
                       url(r'^$', ListArticles.as_view(), name='list'))
