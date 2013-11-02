# coding: utf-8

from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns

import views

urlpatterns = patterns('',

    #API
    url(r'^categories/$', views.CategoryList.as_view()),
    url(r'^categories/(?P<pk>[0-9]+)/$', views.CategoryDetail.as_view()),
    url(r'^forums/$', views.ForumList.as_view()),
    url(r'^forums/(?P<pk>[0-9]+)/$', views.ForumDetail.as_view()),
    url(r'^sujets/$', views.TopicList.as_view()),
    url(r'^sujets/(?P<pk>[0-9]+)/$', views.TopicDetail.as_view()),
    url(r'^sujets/lus/$', views.TopicReadList.as_view()),
    url(r'^sujets/lus/(?P<pk>[0-9]+)/$', views.TopicReadDetail.as_view()),
    url(r'^sujets/suivis/$', views.TopicFollowedList.as_view()),
    url(r'^sujets/suivis/(?P<pk>[0-9]+)/$', views.TopicFollowedDetail.as_view()),
    url(r'^messages/$', views.PostList.as_view()),
    url(r'^messages/(?P<pk>[0-9]+)/$', views.PostDetail.as_view()),

    url(r'^membres/$', views.UserList.as_view()),
    url(r'^membres/(?P<pk>[0-9]+)/$', views.UserDetail.as_view()),

    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
)

urlpatterns = format_suffix_patterns(urlpatterns)
