# coding: utf-8

from django.conf.urls import url

from zds.pages.views import about, association, contact, eula, alerts, cookies, assoc_subscribe, index


urlpatterns = [
    # single pages
    url(r'^apropos/$', about),
    url(r'^association/$', association),
    url(r'^contact/$', contact),
    url(r'^cgu/$', eula),
    url(r'^alertes/$', alerts),
    url(r'^cookies/$', cookies),
    url(r'^association/inscription/$', assoc_subscribe),

    # index
    url(r'^$', index),
]
