# coding: utf-8

from django.conf.urls import patterns, url
from zds.mp.views import PrivateTopicList, PrivatePostList, PrivateTopicNew, AddParticipant, LeaveMP, LeaveList, \
    PrivatePostAnswer


urlpatterns = patterns('',

    # Message-related
    url(r'^message/editer/$', 'zds.mp.views.edit_post'),

    # Topics.
    url(r'^$', PrivateTopicList.as_view(), name='mp-list'),
    url(r'^quitter/$', LeaveList.as_view(), name='mp-list-delete'),
    url(r'^nouveau/$', PrivateTopicNew.as_view(), name='mp-new'),

    url(r'^(?P<pk>\d+)/quitter/$', LeaveMP.as_view(), name='mp-delete'),
    url(r'^(?P<pk>\d+)/editer/participants/$', AddParticipant.as_view(), name='mp-edit-participant'),

    # Posts.
    url(r'^(?P<pk>\d+)/messages/$', PrivatePostList.as_view(), name='posts-private-list'),
    url(r'^(?P<pk>\d+)/message/nouveau/$', PrivatePostAnswer.as_view(), name='posts-private-new'),
)
