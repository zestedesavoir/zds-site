# coding: utf-8

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',

    # Viewing a thread
    url(r'^nouveau$', views.new),
    url(r'^editer$', views.edit),
    url(r'^(?P<topic_pk>\d+)/(?P<topic_slug>.+)$', views.topic),

    # Message-related
    url(r'^message/editer$', views.edit_post),
    url(r'^message/nouveau$', views.answer),
    
    # Home
    url(r'^$', views.index),
)
