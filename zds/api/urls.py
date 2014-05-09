# coding: utf-8

from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^users/$', views.UserList.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view()),

    url(r'^articles/$', views.ArticlePublishedList.as_view()),
    url(r'^forums/$', views.ForumList.as_view()),
    url(r'^topics/$', views.TopicList.as_view()),
    url(r'^posts/$', views.PostList.as_view()),
)
