from django.urls import path, re_path
from django.views.generic.base import RedirectView

from zds.tutorialv2.views.contributors import ContentOfContributors
from zds.tutorialv2.views.lists import TagsListView, ContentOfAuthor
from zds.tutorialv2.views.download_online import DownloadOnlineArticle
from zds.tutorialv2.views.display import DisplayOnlineArticle
from zds.tutorialv2.feeds import LastArticlesFeedRSS, LastArticlesFeedATOM

urlpatterns = [
    # Flux
    re_path(r'^flux/rss/$', LastArticlesFeedRSS(), name='feed-rss'),
    re_path(r'^flux/atom/$', LastArticlesFeedATOM(), name='feed-atom'),

    # View
    re_path(r'^(?P<pk>\d+)/(?P<slug>.+)/$',
            DisplayOnlineArticle.as_view(), name='view'),

    # Downloads
    re_path(r'^md/(?P<pk>\d+)/(?P<slug>.+)\.md$',
            DownloadOnlineArticle.as_view(requested_file='md'), name='download-md'),
    re_path(r'^pdf/(?P<pk>\d+)/(?P<slug>.+)\.pdf$', DownloadOnlineArticle.as_view(requested_file='pdf'),
            name='download-pdf'),
    re_path(r'^tex/(?P<pk>\d+)/(?P<slug>.+)\.tex$', DownloadOnlineArticle.as_view(requested_file='tex'),
            name='download-tex'),
    re_path(r'^epub/(?P<pk>\d+)/(?P<slug>.+)\.epub$', DownloadOnlineArticle.as_view(requested_file='epub'),
            name='download-epub'),
    re_path(r'^zip/(?P<pk>\d+)/(?P<slug>.+)\.zip$', DownloadOnlineArticle.as_view(requested_file='zip'),
            name='download-zip'),

    # Listing
    re_path(r'^$', RedirectView.as_view(
        pattern_name='publication:list', permanent=True)),
    re_path(
        r'tags/*', TagsListView.as_view(displayed_types=['ARTICLE']), name='tags'),

    path('voir/<str:username>/',
         ContentOfAuthor.as_view(
             type='ARTICLE', context_object_name='articles'),
         name='find-article'),
    path('contributions/<str:username>/',
         ContentOfContributors.as_view(
             type='ARTICLE', context_object_name='contribution_articles'),
         name='find-contributions-article'),
]
