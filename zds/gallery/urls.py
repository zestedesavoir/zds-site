from django.conf.urls import url

from zds.gallery.views import NewGallery, NewImage, DeleteImages, EditImage, ImportImages, GalleryDetails, \
    EditGallery, ListGallery, DeleteGalleries, EditGalleryMembers


urlpatterns = [
    # Index
    url(r'^$', ListGallery.as_view(), name='gallery-list'),

    # Gallery operation
    url(r'^nouveau/$', NewGallery.as_view(), name='gallery-new'),
    url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', GalleryDetails.as_view(), name='gallery-details'),
    url(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$', EditGallery.as_view(), name='gallery-edit'),
    url(r'^membres/(?P<pk>\d+)/$', EditGalleryMembers.as_view(), name='gallery-members'),
    url(r'^supprimer/$', DeleteGalleries.as_view(), name='galleries-delete'),

    # Image operations
    url(r'^image/ajouter/(?P<pk_gallery>\d+)/$', NewImage.as_view(), name='gallery-image-new'),
    url(r'^image/supprimer/(?P<pk_gallery>\d+)/$', DeleteImages.as_view(), name='gallery-image-delete'),
    url(r'^image/editer/(?P<pk_gallery>\d+)/(?P<pk>\d+)/$', EditImage.as_view(), name='gallery-image-edit'),
    url(r'^image/importer/(?P<pk_gallery>\d+)/$', ImportImages.as_view(), name='gallery-image-import'),
]
