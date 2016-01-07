# coding: utf-8

from django.conf.urls import url

from zds.pages.views import about, association, contact, eula, alerts, cookies, assoc_subscribe, index


urlpatterns = [
    # single pages
    url(r'^apropos/$', about, name='pages-about'),
    url(r'^association/$', association, name='pages-association'),
    url(r'^contact/$', contact, name='pages-contact'),
    url(r'^cgu/$', eula, name='pages-eula'),
    url(r'^alertes/$', alerts, name='pages-alerts'),
    url(r'^cookies/$', cookies, name='pages-cookies'),
    url(r'^association/inscription/$', assoc_subscribe, name='pages-assoc-subscribe'),

    # index
    url(r'^$', index, name='pages-index'),
]
