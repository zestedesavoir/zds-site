# coding: utf-8

from django.conf.urls import patterns, url

import zds.gallery.views


urlpatterns = patterns('',
    # Add and edit a gallery
    url(r'^nouveau/$', views.NewGallery.as_view(), name='gallery-new'),
    url(r'^modifier/$', 'zds.gallery.views.modify_gallery'),

    # Image operations
    url(r'^image/ajouter/(?P<pk_gallery>\d+)/$', views.NewImage.as_view(), name='gallery-image-new'),
    url(r'^image/supprimer/$', views.DeleteImages.as_view(), name='gallery-image-delete'),
    url(r'^image/editer/(?P<pk_gallery>\d+)/(?P<pk>\d+)/$', views.EditImage.as_view(), name='gallery-image-edit'),
    url(r'^image/importer/(?P<pk_gallery>\d+)/$', views.ImportImages.as_view(), name='gallery-image-import'),

    # View a gallery
    url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', views.GalleryDetails.as_view(), name='gallery-details'),

    # edit a gallery
    url(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$', views.EditGallery.as_view(), name='gallery-edit'),

    # Index
    url(r'^$', views.ListGallery.as_view(), name='gallery-list'),
)
