# coding: utf-8

from django.conf.urls import patterns, url

from zds.news.views import NewsList, NewsCreate, NewsUpdate, NewsDeleteDetail, NewsDeleteList

urlpatterns = patterns('',
                       url(r'^$', NewsList.as_view(), name='news-list'),
                       url(r'^creer/$', NewsCreate.as_view(), name='news-create'),
                       url(r'^editer/(?P<pk>\d+)/$', NewsUpdate.as_view(), name='news-update'),
                       url(r'^supprimer/(?P<pk>\d+)/$', NewsDeleteDetail.as_view(), name='news-delete'),
                       url(r'^supprimer/$', NewsDeleteList.as_view(), name='news-list-delete'),
)
