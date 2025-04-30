from rest_framework import permissions
from rest_framework.generics import get_object_or_404

from zds.mp.models import PrivateTopic


class IsParticipant(permissions.BasePermission):
    """
    Custom permission to know if a member is a participant in a private topic.
    """

    def has_object_permission(self, request, view, obj):
        return obj.is_participant(request.user)


class IsParticipantFromPrivatePost(permissions.BasePermission):
    """
    Custom permission to know if a member is a participant in a private topic from a private post.
    """

    def has_permission(self, request, view):
        private_topic = get_object_or_404(PrivateTopic, pk=view.kwargs.get("pk_ptopic"))
        return private_topic.is_participant(request.user)


class IsNotAloneInPrivatePost(permissions.BasePermission):
    """
    Custom permission to know if a member is the only participant in a private topic.
    """

    def has_permission(self, request, view):
        private_topic = get_object_or_404(PrivateTopic, pk=view.kwargs.get("pk_ptopic"))
        return not private_topic.one_participant_remaining()


class IsLastPrivatePostOfCurrentUser(permissions.BasePermission):
    """
    Custom permission to know if it is the last private post in the private topic.
    """

    def has_object_permission(self, request, view, obj):
        private_topic = get_object_or_404(PrivateTopic, pk=view.kwargs.get("pk_ptopic"))
        return obj.is_last_message(private_topic) and obj.is_author(request.user)


class IsAuthor(permissions.BasePermission):
    """
    Custom permission to know if the user is the author of the private topic.
    """

    def has_object_permission(self, request, view, obj):
        return obj.is_author(request.user)
