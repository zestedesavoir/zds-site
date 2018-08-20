from rest_framework import permissions

from zds.gallery.models import UserGallery


class AccessToGallery(permissions.BasePermission):
    """
    Custom permission to know if a member has access to gallery
    """

    def has_permission(self, request, view):
        return UserGallery.objects.filter(user=request.user, gallery__pk=view.kwargs.get('pk_gallery')).count() == 1
