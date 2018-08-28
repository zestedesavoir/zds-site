from rest_framework import permissions

from zds.gallery.models import UserGallery, Gallery
from zds.tutorialv2.models.database import PublishableContent


class AccessToGallery(permissions.BasePermission):
    """
    Custom permission to know if a member has access to gallery
    """

    def has_permission(self, request, view):
        return UserGallery.objects.filter(user=request.user, gallery__pk=view.kwargs.get('pk_gallery')).exists()


class WriteAccessToGallery(permissions.BasePermission):
    """
    Custom permission to know if a member has write access to gallery
    """

    def has_permission(self, request, view):
        return UserGallery.objects.filter(
            user=request.user, gallery__pk=view.kwargs.get('pk_gallery'), mode='W').exists()


class NotLinkedToContent(permissions.BasePermission):
    """
    Custom permission to denied modification of a gallery linked to a content
    """
    def has_permission(self, request, view):
        return not PublishableContent.objects.filter(gallery__pk=view.kwargs.get('pk_gallery')).exists()

    def has_object_permission(self, request, view, obj):
        gallery = obj if isinstance(obj, Gallery) else obj.gallery
        return not PublishableContent.objects.filter(gallery=gallery).exists()
