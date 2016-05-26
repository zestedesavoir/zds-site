# coding: utf-8

from django.conf.urls import url

from zds.pages.views import about, association, eula, alerts, cookies, index, AssocSubscribeView, ContactView

urlpatterns = [
    # single pages
    url(r'^apropos/$', about, name='pages-about'),
    url(r'^association/$', association, name='pages-association'),
    url(r'^contact/$', ContactView.as_view(), name='pages-contact'),
    url(r'^cgu/$', eula, name='pages-eula'),
    url(r'^alertes/$', alerts, name='pages-alerts'),
    url(r'^cookies/$', cookies, name='pages-cookies'),
    url(r'^association/inscription/$', AssocSubscribeView.as_view(), name='pages-assoc-subscribe'),

    # index
    url(r'^$', index, name='pages-index'),
]
