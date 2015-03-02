# coding: utf-8

from django.conf.urls import patterns, url
from zds.mp.views import PrivateTopicList, PrivatePostList, PrivateTopicNew


urlpatterns = patterns('',

    # Viewing a thread
    url(r'^editer/$', 'zds.mp.views.edit'),
    url(r'^quitter/$', 'zds.mp.views.leave'),
    url(r'^ajouter/$', 'zds.mp.views.add_participant'),

    # Message-related
    url(r'^message/editer/$', 'zds.mp.views.edit_post'),
    url(r'^message/nouveau/$', 'zds.mp.views.answer'),

    # Topics.
    url(r'^$', PrivateTopicList.as_view(), name='mp-list'),
    url(r'^quitter-list/$', 'zds.mp.views.leave_mps'),
    url(r'^nouveau/$', PrivateTopicNew.as_view(), name='mp-new'),

    # Posts.
    url(r'^(?P<pk>\d+)/messages/$', PrivatePostList.as_view(), name='posts-private-list'),
)
