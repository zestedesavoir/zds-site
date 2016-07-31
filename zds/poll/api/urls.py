#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf.urls import url

from zds.poll.api.views import PollDetailAPIView, VoteAPIView

urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/$', PollDetailAPIView.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/vote', VoteAPIView.as_view(), name='vote'),
]
