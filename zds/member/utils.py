#!/usr/bin/python
# -*- coding: utf-8 -*-


def get_next_redirect_url(request, redirect_field_name="next"):
    """
    Returns the next URL to redirect to, if it was explicitly passed
    via the request.
    """
    from django.utils.http import is_safe_url

    redirect_to = request.REQUEST.get(redirect_field_name)
    if not is_safe_url(redirect_to):
        redirect_to = None
    return redirect_to


def get_login_redirect_url(request, url):
    from zds.utils.globals import resolve_url

    assert request.user.is_authenticated()
    return resolve_url(url)


def passthrough_next_redirect_url(request, url, redirect_field_name):
    from django.utils.http import urlencode

    assert url.find("?") < 0
    next_url = get_next_redirect_url(request, redirect_field_name)
    if next_url:
        url = url + '?' + urlencode({redirect_field_name: next_url})
    return url
