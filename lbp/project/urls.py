# encoding: utf-8

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.index),
    url(r'^nouveau$', views.new),
    
    url(r'^voir/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.view_general),
    url(r'^voir/details/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.view_details),
    url(r'^voir/strategie/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.view_strategy),
    url(r'^voir/roadmap/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.view_roadmap),
    url(r'^voir/histoire/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.view_history),
    url(r'^voir/etude-marche/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.view_marketstudy),
    
    url(r'^editer/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.edit_general),
    url(r'^editer/details/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.edit_details),
    url(r'^editer/strategie/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.edit_strategy),
    url(r'^editer/roadmap/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.edit_roadmap),
    url(r'^editer/etude-marche/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.edit_marketstudy),
    
    url(r'^recrutement/(?P<prj_pk>\d+)/(?P<prj_slug>.+)', views.recrutement),
)
