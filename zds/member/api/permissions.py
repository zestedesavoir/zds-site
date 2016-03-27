# -*- coding: utf-8 -*-

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet
        return obj.user == request.user


class IsStaffUser(permissions.BasePermission):
    """
    Allows access only to staff users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.has_perm("member.change_profile")


class CanReadAndWriteNowOrReadOnly(permissions.BasePermission):
    """
    Similar to member.decorator.can_write_and_read_now
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        try:
            profile = request.user.profile
        except:
            # The user is a visitor
            profile = None

        if profile is not None:
            return profile.can_read_now() and profile.can_write_now()

        return True
