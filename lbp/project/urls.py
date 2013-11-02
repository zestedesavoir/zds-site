# encoding: utf-8

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.index),
    url(r'^nouveau$', views.new),
)
