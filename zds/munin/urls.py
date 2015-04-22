# -*- coding: utf-8 -*-:
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',

    url(r'^total_topics/$', views.total_topics),
    url(r'^total_posts/$', views.total_posts),
    url(r'^total_mps/$', views.total_mps),
    url(r'^total_tutorials/$', views.total_tutorials),
    url(r'^total_articles/$', views.total_articles),
)
