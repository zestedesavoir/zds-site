# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.views.views_published import ListOpinions, DisplayOnlineOpinion, DownloadOnlineOpinion
from zds.tutorialv2.feeds import LastOpinionsFeedRSS, LastOpinionsFeedATOM

urlpatterns = [
    # Flux
    url(r'^flux/rss/$', LastOpinionsFeedRSS(), name='feed-rss'),
    url(r'^flux/atom/$', LastOpinionsFeedATOM(), name='feed-atom'),

    # View
    url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayOnlineOpinion.as_view(), name='view'),

    # downloads:
    url(r'^md/(?P<pk>\d+)/(?P<slug>.+)\.md$',
        DownloadOnlineOpinion.as_view(requested_file='md'), name='download-md'),
    url(r'^html/(?P<pk>\d+)/(?P<slug>.+)\.html$',
        DownloadOnlineOpinion.as_view(requested_file='html'), name='download-html'),
    url(r'^pdf/(?P<pk>\d+)/(?P<slug>.+)\.pdf$',
        DownloadOnlineOpinion.as_view(requested_file='pdf'), name='download-pdf'),
    url(r'^epub/(?P<pk>\d+)/(?P<slug>.+)\.epub$',
        DownloadOnlineOpinion.as_view(requested_file='epub'), name='download-epub'),
    url(r'^zip/(?P<pk>\d+)/(?P<slug>.+)\.zip$',
        DownloadOnlineOpinion.as_view(requested_file='zip'), name='download-zip'),

    # Listing
    url(r'^$', ListOpinions.as_view(), name='list')
]
