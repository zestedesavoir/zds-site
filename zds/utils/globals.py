#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.core import urlresolvers
from django.utils import importlib, six


def resolve_url(to):
    """
    Subset of django.shortcuts.resolve_url (that one is 1.5+)
    """
    try:
        return urlresolvers.reverse(to)
    except urlresolvers.NoReverseMatch:
        # If this doesn't "feel" like a URL, re-raise.
        if '/' not in to and '.' not in to:
            raise
    # Finally, fall back and assume it's a URL
    return to


def import_attribute(path):
    assert isinstance(path, six.string_types)
    pkg, attr = path.rsplit('.', 1)
    module = importlib.import_module(pkg)
    ret = getattr(module, attr)
    return ret


def get_class(value):
    if isinstance(value, type):
        return value
    if isinstance(value, basestring):
        try:
            return __import__(value)
        except ImportError:
            raise


def get_form_class(forms, form_id, default_form):
    form_class = forms.get(form_id, default_form)
    if isinstance(form_class, six.string_types):
        form_class = import_attribute(form_class)
    return form_class


def get_client_ip(request):
    """
    Retrieve the real IP address of the client.
    """
    if "HTTP_X_REAL_IP" in request.META:  # nginx
        return request.META.get("HTTP_X_REAL_IP")
    elif "REMOTE_ADDR" in request.META:
        # other
        return request.META.get("REMOTE_ADDR")
    else:
        # should never happend
        return "0.0.0.0"
