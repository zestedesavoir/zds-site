from django.conf import settings
from django.contrib.auth.models import User
from social_django.middleware import SocialAuthExceptionMiddleware
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class ZDSCustomizeSocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    """
    For more information, \
    see http://python-social-auth.readthedocs.io/en/latest/configuration/django.html#exceptions-middleware.
    """

    def get_message(self, request, exception):
        # this message aims to be displayed in our "error" widget
        message = _("Un problème a eu lieu lors de la communication avec le réseau social.")
        logger.warn("Social error %s", exception)
        messages.error(request, message)
        # this one is just for social auth compatibility (will be passed as get param)
        return "Bad communication"

    def get_redirect_uri(self, *_, **__):
        return reverse("member-login")


def get_bot_account() -> User:
    """
    Get the bot account.
    Used for example to send automated private messages.
    """
    return User.objects.get(username=settings.ZDS_APP["member"]["bot_account"])


def get_external_account() -> User:
    """
    Get the external account.
    Used for example to mark publications by authors not registered on the site.
    """
    return User.objects.get(username=settings.ZDS_APP["member"]["external_account"])


def get_anonymous_account() -> User:
    """
    Get the anonymous account.
    Used for example as a replacement for unregistered users.
    """
    return User.objects.get(username=settings.ZDS_APP["member"]["anonymous_account"])
