# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListTutorials
from zds.tutorialv2.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM

urlpatterns = patterns('',
                       # Viewing
                       url(r'^flux/rss/$', LastTutorialsFeedRSS(), name='feed-rss'),
                       url(r'^flux/atom/$', LastTutorialsFeedATOM(), name='feed-atom'),

                       # Listing
                       url(r'^$', ListTutorials.as_view(), name='list'))
