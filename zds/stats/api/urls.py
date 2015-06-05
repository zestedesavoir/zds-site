# coding: utf-8

from django.conf.urls import patterns, url

from zds.stats.api.views import StatContentListAPI, StatContentDetailAPI, StatSourceContentListAPI, StatDeviceContentListAPI, StatBrowserContentListAPI, StatCountryContentListAPI, StatCityContentListAPI, StatOSContentListAPI

urlpatterns = patterns('',
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/$', StatContentDetailAPI.as_view(), name='api-stats-details-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/$', StatContentListAPI.as_view(), name='api-stats-list-content-visits'),
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/sources/$', StatSourceContentListAPI.as_view(), name='api-stats-details-source-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/sources/$', StatSourceContentListAPI.as_view(), name='api-stats-list-source-content-visits'),
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/appareil/$', StatDeviceContentListAPI.as_view(), name='api-stats-details-device-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/appareil/$', StatDeviceContentListAPI.as_view(), name='api-stats-list-device-content-visits'),
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/navigateur/$', StatBrowserContentListAPI.as_view(), name='api-stats-details-browser-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/navigateur/$', StatBrowserContentListAPI.as_view(), name='api-stats-list-browser-content-visits'),
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/pays/$', StatCountryContentListAPI.as_view(), name='api-stats-details-country-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/pays/$', StatCountryContentListAPI.as_view(), name='api-stats-list-country-content-visits'),
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/ville/$', StatCityContentListAPI.as_view(), name='api-stats-details-city-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/ville/$', StatCityContentListAPI.as_view(), name='api-stats-list-city-content-visits'),
                        url(r'^(?P<content_type>.+)/(?P<content_id>[0-9]+)/visites/systeme/$', StatOSContentListAPI.as_view(), name='api-stats-details-os-content-visits'),
                        url(r'^(?P<content_type>.+)/visites/systeme/$', StatOSContentListAPI.as_view(), name='api-stats-list-os-content-visits'),
)