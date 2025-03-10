from django.urls import re_path

from .views import (
    GalleryDetailView,
    GalleryListView,
    ImageDetailView,
    ImageListView,
    ParticipantDetailView,
    ParticipantListView,
)

urlpatterns = [
    re_path(r"^$", GalleryListView.as_view(), name="list"),
    re_path(r"^(?P<pk>[0-9]+)/?$", GalleryDetailView.as_view(), name="detail"),
    re_path(r"^(?P<pk_gallery>[0-9]+)/images/?$", ImageListView.as_view(), name="list-images"),
    re_path(r"^(?P<pk_gallery>[0-9]+)/images/(?P<pk>[0-9]+)?$", ImageDetailView.as_view(), name="detail-image"),
    re_path(r"^(?P<pk_gallery>[0-9]+)/participants/?$", ParticipantListView.as_view(), name="list-participants"),
    re_path(
        r"^(?P<pk_gallery>[0-9]+)/participants/(?P<user__pk>[0-9]+)/?$",
        ParticipantDetailView.as_view(),
        name="detail-participant",
    ),
]
