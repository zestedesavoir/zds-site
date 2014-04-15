# coding: utf-8

from django.conf.urls import patterns, url

import views


urlpatterns = patterns('',

    url(r'^apropos$', views.about),
    url(r'^association', views.association),
    url(r'^contact', views.contact),
    url(r'^cgu', views.eula),

    url(r'^$', views.index),
)
