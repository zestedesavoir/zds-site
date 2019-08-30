from django.urls import re_path

from zds.gallery.forms import DrawingForm
from zds.gallery.models import Drawing
from zds.gallery.views import NewGallery, NewImage, DeleteImages, EditImage, ImportImages, GalleryDetails, \
    EditGallery, ListGallery, DeleteGalleries, EditGalleryMembers, NewDrawing

urlpatterns = [
    # Index
    re_path(r'^$', ListGallery.as_view(), name='gallery-list'),

    # Gallery operation
    re_path(r'^nouveau/$', NewGallery.as_view(), name='gallery-new'),
    re_path(r'^(?P<pk>\d+)/(?P<slug>.+)/$',
            GalleryDetails.as_view(), name='gallery-details'),
    re_path(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$',
            EditGallery.as_view(), name='gallery-edit'),
    re_path(r'^membres/(?P<pk>\d+)/$',
            EditGalleryMembers.as_view(), name='gallery-members'),
    re_path(r'^supprimer/$', DeleteGalleries.as_view(),
            name='galleries-delete'),

    # Image operations
    re_path(r'^image/ajouter/(?P<pk_gallery>\d+)/$',
            NewImage.as_view(), name='gallery-image-new'),
    re_path(r'^dessin/ajouter/(?P<pk_gallery>\d+)/$',
            NewDrawing.as_view(form_class=DrawingForm), name='gallery-drawing-new'),
    re_path(r'^image/supprimer/(?P<pk_gallery>\d+)/$',
            DeleteImages.as_view(), name='gallery-image-delete'),
    re_path(r'^image/editer/(?P<pk_gallery>\d+)/(?P<pk>\d+)/$',
            EditImage.as_view(), name='gallery-image-edit'),
    re_path(r'^dessin/editer/(?P<pk_gallery>\d+)/(?P<pk>\d+)/$',
            EditImage.as_view(template_name='gallery/image/edit-drawing.html', model=Drawing,
                              url_flag='drawing'), name='gallery-drawing-edit'),
    re_path(r'^image/importer/(?P<pk_gallery>\d+)/$',
            ImportImages.as_view(), name='gallery-image-import'),
]
