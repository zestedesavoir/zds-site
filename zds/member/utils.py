import ipaddress
import logging
from importlib import import_module

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.gis.geoip2 import GeoIP2, GeoIP2Exception
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from geoip2.errors import AddressNotFoundError
from oauth2_provider.models import AccessToken
from social_django.middleware import SocialAuthExceptionMiddleware
from ua_parser import user_agent_parser

logger = logging.getLogger(__name__)

Session = import_module(settings.SESSION_ENGINE).CustomSession
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


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


def get_antispam_account() -> User:
    """
    Get the antispam account.
    Used for signaling users as spam.
    """
    return User.objects.get(username=settings.ZDS_APP["member"]["antispam_account"])


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


def remove_session(session_key, user_pk):
    """Removes a session, but checks before that the session belongs to the user."""
    session = SessionStore(session_key=session_key)
    if session.get("_auth_user_id", "") == str(user_pk):
        session.flush()


@transaction.atomic
def unregister(user: User):
    """Unregisters a user: remove all related data, anonymize what we want to keep and remove all sessions."""
    # To avoid circular imports:
    from zds.forum.models import Topic
    from zds.gallery.models import GALLERY_WRITE, UserGallery
    from zds.member.models import Ban, BannedEmailProvider, KarmaNote
    from zds.mp.models import PrivatePost, PrivateTopic
    from zds.tutorialv2.models.database import PickListOperation
    from zds.tutorialv2.models.events import Event
    from zds.utils.models import Alert, Comment, CommentEdit, CommentVote, HatRequest

    anonymous = get_anonymous_account()
    external = get_external_account()

    # Nota : as of v21 all about content paternity is held by a proper receiver in zds.tutorialv2.models.database
    PickListOperation.objects.filter(staff_user=user).update(staff_user=anonymous)
    PickListOperation.objects.filter(canceler_user=user).update(canceler_user=anonymous)

    Event.objects.filter(performer=user).update(performer=external)
    Event.objects.filter(author=user).update(author=external)
    Event.objects.filter(contributor=user).update(contributor=external)

    # Comments likes / dislikes
    votes = CommentVote.objects.filter(user=user)
    for vote in votes:
        if vote.positive:
            vote.comment.like -= 1
        else:
            vote.comment.dislike -= 1
        vote.comment.save()
    votes.delete()
    # All contents anonymization
    Comment.objects.filter(author=user).update(author=anonymous)
    PrivatePost.objects.filter(author=user).update(author=anonymous)
    CommentEdit.objects.filter(editor=user).update(editor=anonymous)
    CommentEdit.objects.filter(deleted_by=user).update(deleted_by=anonymous)
    # Karma notes, alerts and sanctions anonymization (to keep them)
    KarmaNote.objects.filter(moderator=user).update(moderator=anonymous)
    Ban.objects.filter(moderator=user).update(moderator=anonymous)
    Alert.objects.filter(author=user).update(author=anonymous)
    Alert.objects.filter(moderator=user).update(moderator=anonymous)
    BannedEmailProvider.objects.filter(moderator=user).update(moderator=anonymous)
    # Solved hat requests anonymization
    HatRequest.objects.filter(moderator=user).update(moderator=anonymous)
    # In case current user has been moderator in the past
    Comment.objects.filter(editor=user).update(editor=anonymous)
    for topic in PrivateTopic.objects.filter(Q(author=user) | Q(participants__in=[user])):
        if topic.one_participant_remaining():
            topic.delete()
        else:
            topic.remove_participant(user)
            topic.save()
    Topic.objects.filter(solved_by=user).update(solved_by=anonymous)
    Topic.objects.filter(author=user).update(author=anonymous)

    # Any content exclusively owned by the unregistering member will
    # be deleted just before the User object (using a pre_delete
    # receiver).
    #
    # Regarding galleries, there are two cases:
    #
    # - "personal galleries" with one owner (the unregistering
    #   user). The user's ownership is removed and replaced by an
    #   anonymous user in order not to lost the gallery.
    #
    # - "personal galleries" with many other owners. It is safe to
    #   remove the user's ownership, the gallery won't be lost.

    galleries = UserGallery.objects.filter(user=user)
    for gallery in galleries:
        if gallery.gallery.get_linked_users().count() == 1:
            anonymous_gallery = UserGallery()
            anonymous_gallery.user = external
            anonymous_gallery.mode = GALLERY_WRITE
            anonymous_gallery.gallery = gallery.gallery
            anonymous_gallery.save()
    galleries.delete()

    # Remove API access (tokens + applications)
    for token in AccessToken.objects.filter(user=user):
        token.revoke()

    # Remove all sessions to logout the user:
    for session in Session.objects.filter(account_id=user.pk).iterator():
        remove_session(session.session_key, user.pk)
    Session.objects.filter(account_id=user.pk).delete()

    User.objects.filter(pk=user.pk).delete()
