from django.contrib.auth.models import AnonymousUser
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
        if hasattr(obj, "user"):
            author = obj.user
        elif hasattr(obj, "author"):
            author = obj.author
        else:
            author = AnonymousUser()

        return author == request.user


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and self.has_object_permission(request, view, view.get_object())

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user"):
            owners = [obj.user.pk]
        elif hasattr(obj, "author"):
            owners = [obj.author.pk]
        elif hasattr(obj, "authors"):
            owners = list(obj.authors.values_list("pk", flat=True))
        else:
            owners = []
        return request.user.pk in owners


class IsAuthorOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return IsStaffUser().has_permission(request, view) or IsOwner().has_object_permission(
            request, view, view.get_object()
        )


class IsNotOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to prevent owner to vote on their objects
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are not allowed to the owner of the snippet
        if hasattr(obj, "user"):
            author = obj.user
        elif hasattr(obj, "author"):
            author = obj.author
        else:
            author = AnonymousUser()

        return author != request.user


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


class CanReadTopic(permissions.BasePermission):
    """
    Checks if the user can read that topic
    """

    def has_object_permission(self, request, view, obj):
        return obj.topic.forum.can_read(request.user)
