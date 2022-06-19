import re

from django.template import defaultfilters

VALID_SLUG = re.compile(r"^[a-z0-9\-_]+$")

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


def get_current_request():
    return getattr(_thread_locals, "request", None)


class ThreadLocals:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.request = request


def old_slugify(text):
    if not defaultfilters.slugify(text).strip():
        return "--"
    else:
        return defaultfilters.slugify(text)
