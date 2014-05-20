# coding: utf-8

from django.conf.urls import patterns, url


urlpatterns = patterns('',
                       url(r'^$', 'zds.newsletter.views.add_newsletter'),
                       )
