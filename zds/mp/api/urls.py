# coding: utf-8

from django.conf.urls import patterns, url

from zds.mp.api.views import PrivateTopicListAPI

urlpatterns = patterns('',
                       url(r'^$', PrivateTopicListAPI.as_view(), name='api-mp-list'),
)
