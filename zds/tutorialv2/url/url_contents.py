# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListContent, DisplayContent, CreateContent, EditContent, DeleteContent

urlpatterns = patterns('',
                       url(r'^$', ListContent.as_view(), name='index'),

                       # view:
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayContent.as_view(), name='view'),

                       # create:
                       url(r'^nouveau/$', CreateContent.as_view(), name='create'),

                       # edit:
                       url(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$', EditContent.as_view(), name='edit'),

                       # delete:
                       url(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/$', DeleteContent.as_view(), name='delete'),

                       )
