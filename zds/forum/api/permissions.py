# -*- coding: utf-8 -*-

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser



class IsStaffUser(permissions.BasePermission):
    """
    Allows access only to staff users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.has_perm("forum.create_forum")
