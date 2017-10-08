# coding: utf-8

from threading import local

from django.template import defaultfilters


def get_current_user():
    return getattr(local(), 'user', None)


def get_current_request():
    return getattr(local(), 'request', None)


class ThreadLocals(object):

    def process_request(self, request):
        local().user = getattr(request, 'user', None)
        local().request = request


def slugify(text):
    if not defaultfilters.slugify(text).strip():
        return '--'
    else:
        return defaultfilters.slugify(text)
