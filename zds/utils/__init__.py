from django.template import defaultfilters


try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class ThreadLocals(object):

    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.request = request


def slugify(text):
    if not defaultfilters.slugify(text).strip():
        return '--'
    else:
        return defaultfilters.slugify(text)
