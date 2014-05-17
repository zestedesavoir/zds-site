# coding: utf-8

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
                       # Viewing a gallery
                       url(r'^nouveau/$', 'zds.gallery.views.new_gallery'),
                       url(r'^modifier/$', 'zds.gallery.views.modify_gallery'),
                       url(r'^(?P<gal_pk>\d+)/(?P<gal_slug>.+)/$',
                           'zds.gallery.views.gallery_details'),
                       url(r'^$', 'zds.gallery.views.gallery_list'),
                       url(r'^image/ajouter/(?P<gal_pk>\d+)/$',
                           'zds.gallery.views.new_image'),
                       url(r'^image/modifier/$', 'zds.gallery.views.modify_image'),
                       url(r'^image/editer/(?P<gal_pk>\d+)/(?P<img_pk>\d+)/$',
                           'zds.gallery.views.edit_image'),
                       )
