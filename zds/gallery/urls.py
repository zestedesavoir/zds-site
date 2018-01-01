from django.conf.urls import url

from zds.gallery.views import NewGallery, NewImage, DeleteImages, EditImage, ImportImages, GalleryDetails, \
    EditGallery, ListGallery, modify_gallery


urlpatterns = [
    # Add and edit a gallery
    url(r'^nouveau/$', NewGallery.as_view(), name='gallery-new'),
    url(r'^modifier/$', modify_gallery, name='gallery-modify'),

    # Image operations
    url(r'^image/ajouter/(?P<pk_gallery>\d+)/$', NewImage.as_view(), name='gallery-image-new'),
    url(r'^image/supprimer/$', DeleteImages.as_view(), name='gallery-image-delete'),
    url(r'^image/editer/(?P<pk_gallery>\d+)/(?P<pk>\d+)/$', EditImage.as_view(), name='gallery-image-edit'),
    url(r'^image/importer/(?P<pk_gallery>\d+)/$', ImportImages.as_view(), name='gallery-image-import'),

    # View a gallery
    url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', GalleryDetails.as_view(), name='gallery-details'),

    # edit a gallery
    url(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$', EditGallery.as_view(), name='gallery-edit'),

    # Index
    url(r'^$', ListGallery.as_view(), name='gallery-list'),
]
