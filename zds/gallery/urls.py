from django.urls import path

from zds.gallery.views import (
    DeleteGalleries,
    DeleteImages,
    EditGallery,
    EditGalleryMembers,
    EditImage,
    GalleryDetails,
    ImportImages,
    ListGallery,
    NewGallery,
    NewImage,
)

app_name = "gallery"

urlpatterns = [
    # Index
    path("", ListGallery.as_view(), name="list"),
    # Gallery operations
    path("creer/", NewGallery.as_view(), name="create"),
    path("<int:pk>/<slug:slug>/", GalleryDetails.as_view(), name="details"),
    path("modifier/<int:pk>/", EditGallery.as_view(), name="edit"),
    path("membres/<int:pk>/", EditGalleryMembers.as_view(), name="members"),
    path("supprimer/", DeleteGalleries.as_view(), name="delete"),
    # Image operations
    path("<int:pk_gallery>/image/ajouter/", NewImage.as_view(), name="image-add"),
    path("<int:pk_gallery>/image/supprimer/", DeleteImages.as_view(), name="image-delete"),
    path("<int:pk_gallery>/image/<int:pk>/modifier/", EditImage.as_view(), name="image-edit"),
    path("<int:pk_gallery>/image/importer/", ImportImages.as_view(), name="image-import"),
]
