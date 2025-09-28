import ipaddress
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.gis.geoip2 import GeoIP2, GeoIP2Exception
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from geoip2.errors import AddressNotFoundError
from social_django.middleware import SocialAuthExceptionMiddleware
from ua_parser import user_agent_parser

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


def get_geo_location_from_ip(ip: str) -> str:
    """
    Uses geo-localization to get physical localization of an IP address.
    This works relatively well with IPv4 addresses (~city level), but is very
    imprecise with IPv6 or exotic internet providers.
    :return: The city and the country name of this IP.
    """
    try:
        geo = GeoIP2().city(ip)
    except AddressNotFoundError:
        return ""
    except GeoIP2Exception as e:
        logger.warning(
            f"GeoIP2 failed with the following message: '{e}'. "
            "The Geolite2 database might not be installed or configured correctly. "
            "Check the documentation for guidance on how to install it properly."
        )
        return ""
    else:
        city = geo["city"]
        country = geo["country_name"]
        return ", ".join(i for i in [city, country] if i)


def get_info_from_user_agent(user_agent):
    """Parse the user agent and extract information about the device, OS and browser."""

    parsed_ua = user_agent_parser.Parse(user_agent)
    device = parsed_ua["device"]["family"]
    os = user_agent_parser.PrettyOS(*parsed_ua["os"].values())
    browser = user_agent_parser.PrettyUserAgent(*parsed_ua["user_agent"].values())

    return f"{device} / {os} / {browser}"


def get_client_ip(request):
    """Retrieve the real IP address of the client."""

    if "HTTP_X_REAL_IP" in request.META:  # nginx
        return request.META.get("HTTP_X_REAL_IP")
    elif "REMOTE_ADDR" in request.META:
        # other
        return request.META.get("REMOTE_ADDR")
    else:
        # Should never happen
        return "0.0.0.0"


def is_valid_ip(ip_address):
    """Checks if this input is a valid IP address."""
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    else:
        return True


def is_ipv6(ip_address):
    """Checks if this IP address is an IPv6"""
    return ipaddress.ip_address(ip_address).version == 6


def get_network_ip(ip_address):
    """Retrieve the network address of this IP address"""
    return ipaddress.ip_network(ip_address + "/64", strict=False)


def get_network_ip_filter(ip_address):
    """Retrieves the network address of this IP address without the last colon, so we can filter IP addresses on this network"""
    return str(get_network_ip(ip_address).network_address)[:-1]
