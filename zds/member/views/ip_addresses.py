import ipaddress

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from zds.member.decorator import LoginRequiredMixin
from zds.member.forms import BlockedIPForm
from zds.member.models import BlockedIP, Profile
from zds.member.utils import get_geo_location_from_ip
from zds.utils.paginator import ZdSPagingListView


class BlockedIPListView(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permission_required = "member.change_blockedip"
    paginate_by = settings.ZDS_APP["member"]["providers_per_page"]

    model = BlockedIP
    context_object_name = "blocked_ips"
    template_name = "member/admin/list-blocked-ips.html"
    queryset = (
        BlockedIP.objects.select_related("moderator").select_related("moderator__profile").order_by("-blocked_date")
    )


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

    ip_is_already_blocked = BlockedIP.objects.is_blocked(ip_address)
    members = Profile.objects.filter(last_ip_address=ip_address).order_by("-last_visit")
    context_data = {
        "members": members,
        "ip": ip_address,
        "ip_location": get_geo_location_from_ip(ip_address),
        "ip_is_already_blocked": ip_is_already_blocked,
    }

    ipv6 = False
    if ":" in ip_address:  # Check if it's an IPv6
        network_ip = ipaddress.ip_network(ip_address + "/64", strict=False).network_address  # Get the network / block
        # Remove the additional ":" at the end of the network address, so we can filter the IP adresses on this network
        network_ip = str(network_ip)[:-1]
        network_members = Profile.objects.filter(last_ip_address__startswith=network_ip).order_by("-last_visit")
        context_data["network_members"] = network_members
        context_data["network_ip"] = network_ip
        ipv6 = True

    if request.method == "POST":
        form = BlockedIPForm(ipv6, request.POST)
        if form.is_valid():
            if not ip_is_already_blocked:
                BlockedIP(
                    ip_address=ip_address,
                    is_network_address=form.data["is_network_address"],
                    moderator=request.user,
                    reason=form.data["reason"],
                ).save()
                messages.success(request, "Cette adresse IP a été bloquée !")
                context_data["ip_is_already_blocked"] = True
            else:
                messages.error(request, "Cette adresse IP est déjà bloquée.")
    else:
        form = BlockedIPForm(ipv6)

    context_data["blocked_ip_form"] = form

    return render(request, "member/admin/memberip.html", context_data)
