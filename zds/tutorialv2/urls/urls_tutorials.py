from django.urls import re_path
from django.views.generic.base import RedirectView
from zds.tutorialv2.views.contents import RedirectOldBetaTuto

from zds.tutorialv2.views.published import DisplayOnlineTutorial, DisplayOnlineContainer, \
    DownloadOnlineTutorial, RedirectContentSEO, TagsListView
from zds.tutorialv2.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM


urlpatterns = [
    # flux
    re_path(r'^flux/rss/$', LastTutorialsFeedRSS(), name='feed-rss'),
    re_path(r'^flux/atom/$', LastTutorialsFeedATOM(), name='feed-atom'),

    # view
    re_path(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<p2>\d+)/(?P<parent_container_slug>.+)/(?P<p3>\d+)/(?P<container_slug>.+)/$',
            RedirectContentSEO.as_view(), name='redirect_old_tuto'),
    re_path(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
            DisplayOnlineContainer.as_view(),
            name='view-container'),
    re_path(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
            DisplayOnlineContainer.as_view(),
            name='view-container'),

    re_path(r'^(?P<pk>\d+)/(?P<slug>.+)/$',
            DisplayOnlineTutorial.as_view(), name='view'),

    # downloads:
    re_path(r'^md/(?P<pk>\d+)/(?P<slug>.+)\.md$',
            DownloadOnlineTutorial.as_view(requested_file='md'), name='download-md'),
    re_path(r'^html/(?P<pk>\d+)/(?P<slug>.+)\.html$',
            DownloadOnlineTutorial.as_view(requested_file='html'), name='download-html'),
    re_path(r'^pdf/(?P<pk>\d+)/(?P<slug>.+)\.pdf$',
            DownloadOnlineTutorial.as_view(requested_file='pdf'), name='download-pdf'),
    re_path(r'^epub/(?P<pk>\d+)/(?P<slug>.+)\.epub$',
            DownloadOnlineTutorial.as_view(requested_file='epub'), name='download-epub'),
    re_path(r'^zip/(?P<pk>\d+)/(?P<slug>.+)\.zip$',
            DownloadOnlineTutorial.as_view(requested_file='zip'), name='download-zip'),
    re_path(r'^tex/(?P<pk>\d+)/(?P<slug>.+)\.tex$', DownloadOnlineTutorial.as_view(requested_file='tex'),
            name='download-tex'),

    #  Old beta url compatibility
    re_path('^beta/(?P<pk>\d+)/(?P<slug>.+)',
            RedirectOldBetaTuto.as_view(), name='old-beta-url'),

    # Listing
    re_path(r'^$', RedirectView.as_view(
            pattern_name='publication:list', permanent=True)),
    re_path(r'tags/$',
            TagsListView.as_view(displayed_types=['TUTORIAL']), name='tags')
]
