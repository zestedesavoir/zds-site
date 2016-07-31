#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from zds.poll.views import ListPoll, NewPoll, DetailsPoll,\
    DeletePoll, UpdatePoll

urlpatterns = [
    url(r'^$', ListPoll.as_view(), name='poll-list'),
    url(r'^nouveau/$', NewPoll.as_view(), name='poll-new'),
    url(r'^(?P<pk>\d+)/$', DetailsPoll.as_view(), name='poll-details'),
    url(r'^(?P<pk>\d+)/update', UpdatePoll.as_view(), name='poll-update'),
    url(r'^(?P<pk>\d+)/delete$', DeletePoll.as_view(), name='poll-delete'),
]
