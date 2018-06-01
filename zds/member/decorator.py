from django.contrib.auth.decorators import login_required

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


class PermissionRequiredMixin(object):
    """
    Represent the basic code that a Generic Class Based View has to use when one or more
    permissions are required simultaneously to execute the view
    """
    permissions = []

    def check_permissions(self):
        if False in [self.request.user.has_perm(p) for p in self.permissions]:
            raise PermissionDenied

    def dispatch(self, *args, **kwargs):
        self.check_permissions()
        return super(PermissionRequiredMixin, self).dispatch(*args, **kwargs)


class LoginRequiredMixin(object):
    """
    Represent the basic code that a Generic Class Based View has to use when
    the required action needs the user to be logged in.
    If the user is not logged in, the user is redirected to the connection form and the former action
    is not executed.
    """
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class LoggedWithReadWriteHability(LoginRequiredMixin):
    """
    Represent the basic code that a Generic Class View has to use when a logged in user with
    read and write hability is required.
    """
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(LoggedWithReadWriteHability, self).dispatch(*args, **kwargs)
