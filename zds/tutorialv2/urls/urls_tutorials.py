# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListTutorials, DisplayOnlineTutorial, DisplayOnlineContainer
from zds.tutorialv2.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM

urlpatterns = patterns('',
                       # flux
                       url(r'^flux/rss/$', LastTutorialsFeedRSS(), name='feed-rss'),
                       url(r'^flux/atom/$', LastTutorialsFeedATOM(), name='feed-atom'),

                       # view
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
                           DisplayOnlineContainer.as_view(),
                           name='view-container'),
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           DisplayOnlineContainer.as_view(),
                           name='view-container'),

                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayOnlineTutorial.as_view(), name='view'),

                       # Listing
                       url(r'^$', ListTutorials.as_view(), name='list'))
