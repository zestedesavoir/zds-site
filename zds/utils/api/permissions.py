from rest_framework import permissions


class UpdatePotentialSpamPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    def has_permission(self, request, view):
        return request.user.has_perm("utils.change_comment_potential_spam")
