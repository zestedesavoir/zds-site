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
