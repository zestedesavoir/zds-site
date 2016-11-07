# coding: utf-8

from django.conf.urls import url

from zds.stats.api.views import StatContentListAPI, StatContentDetailAPI, StatSourceContentListAPI,\
    StatDeviceContentListAPI, StatBrowserContentListAPI, StatCountryContentListAPI, StatCityContentListAPI,\
    StatOSContentListAPI

urlpatterns = [
    url(r'^$', StatContentListAPI.as_view(), name='list'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/$',
        StatContentDetailAPI.as_view(),
        name='details-content-visits'),
    url(r'^(?P<content_type>.+)/visites/$', StatContentListAPI.as_view(), name='list-content-visits'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/sources/$',
        StatSourceContentListAPI.as_view(),
        name='details-source-content-visits'),
    url(r'^(?P<content_type>.+)/visites/sources/$',
        StatSourceContentListAPI.as_view(),
        name='list-source-content-visits'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/appareil/$',
        StatDeviceContentListAPI.as_view(),
        name='details-device-content-visits'),
    url(r'^(?P<content_type>.+)/visites/appareil/$',
        StatDeviceContentListAPI.as_view(),
        name='list-device-content-visits'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/navigateur/$',
        StatBrowserContentListAPI.as_view(),
        name='details-browser-content-visits'),
    url(r'^(?P<content_type>.+)/visites/navigateur/$',
        StatBrowserContentListAPI.as_view(),
        name='list-browser-content-visits'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/pays/$',
        StatCountryContentListAPI.as_view(),
        name='details-country-content-visits'),
    url(r'^(?P<content_type>.+)/visites/pays/$',
        StatCountryContentListAPI.as_view(),
        name='list-country-content-visits'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/ville/$',
        StatCityContentListAPI.as_view(),
        name='details-city-content-visits'),
    url(r'^(?P<content_type>.+)/visites/ville/$',
        StatCityContentListAPI.as_view(),
        name='list-city-content-visits'),
    url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/systeme/$',
        StatOSContentListAPI.as_view(),
        name='details-os-content-visits'),
    url(r'^(?P<content_type>.+)/visites/systeme/$',
        StatOSContentListAPI.as_view(),
        name='list-os-content-visits'),
]
