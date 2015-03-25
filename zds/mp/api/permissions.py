# -*- coding: utf-8 -*-

from rest_framework import permissions


class IsParticipant(permissions.BasePermission):
    """
    Custom permission to know if a member is a participant in a private topic.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user in obj.participants.all()
