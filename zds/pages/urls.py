# coding: utf-8

from django.conf.urls import patterns, url


urlpatterns = [
    # single pages
    url(r'^apropos/$', 'zds.pages.views.about'),
    url(r'^association/$', 'zds.pages.views.association'),
    url(r'^contact/$', 'zds.pages.views.contact'),
    url(r'^cgu/$', 'zds.pages.views.eula'),
    url(r'^alertes/$', 'zds.pages.views.alerts'),
    url(r'^cookies/$', 'zds.pages.views.cookies'),
    url(r'^association/inscription/$', 'zds.pages.views.assoc_subscribe'),

    # index
    url(r'^$', 'zds.pages.views.index'),
]
