import ipaddress
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_ipv46_address
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from zds.member.commons import (
    BanSanction,
    DeleteBanSanction,
    DeleteReadingOnlySanction,
    ReadingOnlySanction,
    TemporaryBanSanction,
    TemporaryReadingOnlySanction,
)
from zds.member.decorator import can_write_and_read_now
from zds.member.forms import MiniProfileForm
from zds.member.models import KarmaNote, Profile
from zds.member.utils import get_geo_location_from_ip


@login_required
@permission_required("member.change_profile", raise_exception=True)
def member_from_ip(request, ip_address):
    """List users connected from a particular IP, and an IPv6 subnetwork."""

    # If we don't check if the ip_address has a valid format, two things can
    # happen:
    # - the list of members with this IP will be empty (that's fine)
    # - the call to get_geo_location_from_ip() will raise a ValueError, which
    #   in production will turn into an error 500 (which is not fine)
    try:
        validate_ipv46_address(ip_address)
    except ValidationError:
        raise Http404(_("Mauvais format d'adresse IP"))

    members = Profile.objects.filter(last_ip_address=ip_address).order_by("-last_visit")
    context_data = {
        "members": members,
        "ip": ip_address,
        "ip_location": get_geo_location_from_ip(ip_address),
    }

    if ":" in ip_address:  # Check if it's an IPv6
        network_ip = ipaddress.ip_network(ip_address + "/64", strict=False).network_address  # Get the network / block
        # Remove the additional ":" at the end of the network address, so we can filter the IP adresses on this network
        network_ip = str(network_ip)[:-1]
        network_members = Profile.objects.filter(last_ip_address__startswith=network_ip).order_by("-last_visit")
        context_data["network_members"] = network_members
        context_data["network_ip"] = network_ip

    return render(request, "member/admin/memberip.html", context_data)


@login_required
@permission_required("member.change_profile", raise_exception=True)
@require_POST
def modify_karma(request):
    """Add a Karma note to a user profile."""

    try:
        profile_pk = int(request.POST["profile_pk"])
    except (KeyError, ValueError):
        raise Http404

    profile = get_object_or_404(Profile, pk=profile_pk)
    if profile.is_private():
        raise PermissionDenied

    note = KarmaNote(user=profile.user, moderator=request.user, note=request.POST.get("note", "").strip())

    try:
        note.karma = int(request.POST["karma"])
    except (KeyError, ValueError):
        note.karma = 0

    try:
        if not note.note:
            raise ValueError("note cannot be empty")
        elif note.karma > 100 or note.karma < -100:
            raise ValueError(f"Max karma amount has to be between -100 and 100, you entered {note.karma}")
        else:
            note.save()
            profile.karma += note.karma
            profile.save()
    except ValueError as e:
        logging.getLogger(__name__).warning(f"ValueError: modifying karma failed because {e}")

    return redirect(reverse("member-detail", args=[profile.user.username]))


@can_write_and_read_now
@login_required
@permission_required("member.change_profile", raise_exception=True)
def settings_mini_profile(request, user_name):
    """Minimal settings of users for staff."""

    # Extra information about the current user
    profile = get_object_or_404(Profile, user__username=user_name)
    if request.method == "POST":
        form = MiniProfileForm(request.POST)
        data = {"form": form, "profile": profile}
        if form.is_valid():
            profile.biography = form.data["biography"]
            profile.site = form.data["site"]
            profile.avatar_url = form.data["avatar_url"]
            profile.sign = form.data["sign"]

            # Save profile and redirect user to the settings page
            # with a message indicating the operation state.

            try:
                profile.save()
            except:
                messages.error(request, _("Une erreur est survenue."))
                return redirect(reverse("member-settings-mini-profile"))

            messages.success(request, _("Le profil a correctement été mis à jour."))
            return redirect(reverse("member-detail", args=[profile.user.username]))
        else:
            return render(request, "member/settings/profile.html", data)
    else:
        form = MiniProfileForm(
            initial={
                "biography": profile.biography,
                "site": profile.site,
                "avatar_url": profile.avatar_url,
                "sign": profile.sign,
            }
        )
        data = {"form": form, "profile": profile}
        messages.warning(
            request,
            _(
                "Le profil que vous éditez n'est pas le vôtre. "
                "Soyez encore plus prudent lors de l'édition de celui-ci !"
            ),
        )
        return render(request, "member/settings/profile.html", data)


@require_POST
@can_write_and_read_now
@login_required
@permission_required("member.change_profile", raise_exception=True)
@transaction.atomic
def modify_profile(request, user_pk):
    """Modify the sanction of a user if there is a POST request."""

    profile = get_object_or_404(Profile, user__pk=user_pk)
    if profile.is_private():
        raise PermissionDenied
    if request.user.profile == profile:
        messages.error(request, _("Vous ne pouvez pas vous sanctionner vous-même !"))
        raise PermissionDenied

    if "ls" in request.POST:
        state = ReadingOnlySanction(request.POST)
    elif "ls-temp" in request.POST:
        state = TemporaryReadingOnlySanction(request.POST)
    elif "ban" in request.POST:
        state = BanSanction(request.POST)
    elif "ban-temp" in request.POST:
        state = TemporaryBanSanction(request.POST)
    elif "un-ls" in request.POST:
        state = DeleteReadingOnlySanction(request.POST)
    else:
        # un-ban
        state = DeleteBanSanction(request.POST)

    try:
        ban = state.get_sanction(request.user, profile.user)
    except (ValueError, TypeError):
        # These exception can be raised if content of the POST parameters are
        # not correctly (eg, empty string instead of integer), making the
        # object state having invalid data. The validity of parameters should
        # be checked when creating the `state` object above.
        messages.error(request, _("Une erreur est survenue lors de la récupération de la sanction."))
    else:
        state.apply_sanction(profile, ban)

        if "un-ls" in request.POST or "un-ban" in request.POST:
            msg = state.get_message_unsanction()
        else:
            msg = state.get_message_sanction()

        msg = msg.format(
            ban.user, ban.moderator, ban.type, state.get_detail(), ban.note, settings.ZDS_APP["site"]["literal_name"]
        )

        state.notify_member(ban, msg)

    return redirect(profile.get_absolute_url())
