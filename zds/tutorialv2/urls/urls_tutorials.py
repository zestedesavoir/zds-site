# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListTutorials, DisplayOnlineTutorial, DisplayOnlineContainer, DownloadOnlineTutorial
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

                       # downloads:
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)\.md$',
                           DownloadOnlineTutorial.as_view(requested_file='md'), name='download-md'),
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)\.html$',
                           DownloadOnlineTutorial.as_view(requested_file='html'), name='download-html'),
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)\.pdf$',
                           DownloadOnlineTutorial.as_view(requested_file='pdf'), name='download-pdf'),
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)\.epub$',
                           DownloadOnlineTutorial.as_view(requested_file='epub'), name='download-epub'),

                       # Listing
                       url(r'^$', ListTutorials.as_view(), name='list'))
