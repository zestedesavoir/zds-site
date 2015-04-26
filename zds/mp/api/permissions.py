# -*- coding: utf-8 -*-

from rest_framework import permissions
from rest_framework.generics import get_object_or_404
from zds.mp.models import PrivateTopic


class IsParticipant(permissions.BasePermission):
    """
    Custom permission to know if a member is a participant in a private topic.
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user in obj.participants.all()


class IsParticipantFromPrivatePost(permissions.BasePermission):
    """
    Custom permission to know if a member is a participant in a private topic from a private post.
    """

    def has_permission(self, request, view):
        private_topic = get_object_or_404(PrivateTopic, pk=view.kwargs.get('pk_ptopic'))
        return private_topic.author == request.user or request.user in private_topic.participants.all()
