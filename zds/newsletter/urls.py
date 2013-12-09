# coding: utf-8

from django.conf.urls import patterns, url

import views


urlpatterns = patterns('',
    url(r'^$', views.add_newsletter),
)
