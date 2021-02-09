from rest_framework import permissions


class UpdatePotentialSpamPermission(permissions.BasePermission):
    """
    Permission to use the API to mark a comment as (non)spam.
    """

    def has_permission(self, request, view):
        return request.user.has_perm("utils.change_comment_potential_spam")
