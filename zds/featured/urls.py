# coding: utf-8

from django.conf.urls import patterns, url

from zds.featured.views import ResourceFeaturedList, ResourceFeaturedCreate, ResourceFeaturedUpdate, ResourceFeaturedDeleteDetail, ResourceFeaturedDeleteList, MessageFeaturedCreateUpdate

urlpatterns = patterns('',
                       url(r'^$', ResourceFeaturedList.as_view(), name='featured-list'),
                       url(r'^creer/$', ResourceFeaturedCreate.as_view(), name='featured-create'),
                       url(r'^editer/(?P<pk>\d+)/$', ResourceFeaturedUpdate.as_view(), name='featured-update'),
                       url(r'^supprimer/(?P<pk>\d+)/$', ResourceFeaturedDeleteDetail.as_view(), name='featured-delete'),
                       url(r'^supprimer/$', ResourceFeaturedDeleteList.as_view(), name='featured-list-delete'),
                       url(r'^message/modifier/$', MessageFeaturedCreateUpdate.as_view(), name='featured-message-create'),
)
