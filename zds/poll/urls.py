#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from zds.poll.views import ListPoll, NewPoll, DetailsPoll

urlpatterns = patterns('',
    url(r'^$', ListPoll.as_view(), name='poll-list'),
    url(r'^nouveau/$', NewPoll.as_view(), name='poll-new'),
    url(r'^(?P<pk>\d+)/$', DetailsPoll.as_view(), name='poll-details'),

)
