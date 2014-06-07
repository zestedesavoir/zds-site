# coding: utf-8

from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied


def can_write_and_read_now(func):
    """Decorator to check that the user can read and write now."""
    def _can_write_and_read_now(request, *args, **kwargs):
        try:
            profile = request.user.profile
        except:
            # The user is a visitor
            profile = None

        if profile is not None:
            if not profile.can_read_now() or not profile.can_write_now():
                raise PermissionDenied

        return func(request, *args, **kwargs)
    return _can_write_and_read_now
