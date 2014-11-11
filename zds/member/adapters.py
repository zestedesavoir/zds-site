#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, get_object_or_404

from zds.utils.globals import import_attribute, resolve_url, get_client_ip
from .utils import get_next_redirect_url, get_login_redirect_url
from .models import Profile
from .settings import app_settings


class DefaultMemberAdapter(object):
    def get_login_redirect_url(self, request, url=None, redirect_field_name="next"):
        redirect_url = (
            url
            or get_next_redirect_url(request,
                                     redirect_field_name=redirect_field_name)
            or get_login_redirect_url(request, app_settings.LOGIN_REDIRECT_URL))
        return redirect_url

    def perform_login(self, request, user, redirect_url):
        profile = get_object_or_404(Profile, user=user)
        if not user.is_active:
            messages.error(request,
                           "Vous n'avez pas encore activé votre compte, "
                           "vous devez le faire pour pouvoir vous "
                           "connecter sur le site. Regardez dans vos "
                           "mails : " + str(self.user.email))
            return redirect(resolve_url(app_settings.LOGIN_REDIRECT_URL))

        if not profile.can_read_now():
            messages.error(request,
                           "Vous n'êtes pas autorisé à vous connecter "
                           "sur le site, vous avez été banni par un "
                           "modérateur")
            return redirect(resolve_url(app_settings.LOGIN_REDIRECT_URL))

        login(request, user)

        profile.last_ip_address = get_client_ip(request)
        profile.save()
        return redirect(get_login_redirect_url(request, redirect_url))

    def perform_logout(self, request):
        if request.user.is_authenticated():
            logout(request)
            request.session.clear()
        return redirect(resolve_url("zds.pages.views.home"))


def get_adapter():
    """
    Gets the right adapter according to the value specified
    in the settings of the member module.
    """
    return import_attribute(app_settings.ADAPTER)()