# coding: utf-8

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',

                       # Viewing a thread
                       url(r'^nouveau/$', 'zds.mp.views.new'),
                       url(r'^editer/$', 'zds.mp.views.edit'),
                       url(r'^quitter/$', 'zds.mp.views.leave'),
                       url(r'^ajouter/$', 'zds.mp.views.add_participant'),
                       url(r'^(?P<topic_pk>\d+)/(?P<topic_slug>.+)/$',
                           'zds.mp.views.topic'),

                       # Message-related
                       url(r'^message/editer/$', 'zds.mp.views.edit_post'),
                       url(r'^message/nouveau/$', 'zds.mp.views.answer'),

                       # Home
                       url(r'^$', 'zds.mp.views.index'),
                       )
