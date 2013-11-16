# coding: utf-8

from django.conf.urls import patterns, url

import views


urlpatterns = patterns('',

    # Markdown helper
    url(r'^markdown$', views.help_markdown),
    url(r'^apropos$', views.about),
    url(r'^roadmap$', views.roadmap),

    url(r'^$', views.index),
)
