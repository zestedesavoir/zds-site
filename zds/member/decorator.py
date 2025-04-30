from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator


def can_write_and_read_now(func):
    """
    Checks if the current user has read and write rights, right now.
    A visitor has correct rights only if it is connected and has proper rights attached to its profile.
    Real roles in database are checked, this doesn't use session-cached stuff.
    :param func: the decorated function
    :return: `True` if the current user can read and write, `False` otherwise.
    """

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


class LoggedWithReadWriteHability(LoginRequiredMixin):
    """
    Represent the basic code that a Generic Class View has to use when a logged in user with
    read and write hability is required.
    """

    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
