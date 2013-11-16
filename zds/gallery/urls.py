# coding: utf-8

from django.conf.urls import patterns, url

import views


urlpatterns = patterns('',
     # Viewing a gallery
    url(r'^nouveau$', views.new_gallery),
    url(r'^modifier$', views.modify_gallery),
    url(r'^(?P<gal_pk>\d+)/(?P<gal_slug>.+)', views.gallery_details),
    url(r'^$', views.gallery_list),
    url(r'^image/ajouter/(?P<gal_pk>\d+)$', views.new_image),
    url(r'^image/modifier$', views.modify_image),
    url(r'^image/editer/(?P<gal_pk>\d+)/(?P<img_pk>\d+)$', views.edit_image),
)
