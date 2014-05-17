# coding: utf-8

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',

                       url(r'^apropos/$', 'zds.pages.views.about'),
                       url(r'^association/', 'zds.pages.views.association'),
                       url(r'^contact/', 'zds.pages.views.contact'),
                       url(r'^cgu/', 'zds.pages.views.eula'),
                                              
                       url(r'^alertes/', 'zds.pages.views.alerts'),

                       url(r'^$', 'zds.pages.views.index'),
                       )
