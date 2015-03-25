# coding: utf-8

from django.conf.urls import patterns, url

from zds.mp.api.views import PrivateTopicListAPI, PrivateTopicDetailAPI

urlpatterns = patterns('',
                       url(r'^$', PrivateTopicListAPI.as_view(), name='api-mp-list'),
                       url(r'^(?P<pk>[0-9]+)/$', PrivateTopicDetailAPI.as_view(), name='api-mp-detail'),
)
