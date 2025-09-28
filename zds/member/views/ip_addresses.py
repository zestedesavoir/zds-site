from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from zds.member.decorator import LoginRequiredMixin
from zds.member.forms import BlockedIPForm
from zds.member.models import BlockedIP, Profile
from zds.member.utils import get_geo_location_from_ip, get_network_ip, get_network_ip_filter, is_ipv6, is_valid_ip
from zds.utils.paginator import ZdSPagingListView


class BlockedIPListView(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permission_required = "member.change_blockedip"
    paginate_by = settings.ZDS_APP["member"]["providers_per_page"]

    model = BlockedIP
    context_object_name = "blocked_ips"
    template_name = "member/admin/blocked_ips.html"
    queryset = (
        BlockedIP.objects.select_related("moderator").select_related("moderator__profile").order_by("-blocked_date")
    )


@login_required
@permission_required("member.change_blockedip", raise_exception=True)
def members_from_ip(request, ip_address):
    """List users connected from a particular IP, and an IPv6 subnetwork."""

    # If we don't check if the ip_address has a valid format, two things can
    # happen:
    # - the list of members with this IP will be empty (that's fine)
    # - the call to get_geo_location_from_ip() will raise a ValueError, which
    #   in production will turn into an error 500 (which is not fine)
    if not is_valid_ip(ip_address):
        raise Http404(_("Cette adresse IP n'est pas valide."))

    blocked_ips = BlockedIP.objects.get_details(ip_address)
    ip_is_already_blocked = True if blocked_ips else False
    is_ipv6_ = is_ipv6(ip_address)

    if request.method == "POST":
        form = BlockedIPForm(is_ipv6_, request.POST)
        if form.is_valid():
            if ip_is_already_blocked:
                messages.error(request, "Cette adresse IP est déjà bloquée.")
            else:
                blocked_ip = BlockedIP(
                    ip_address=ip_address,
                    is_network_address=form.data["is_network_address"],
                    moderator=request.user,
                    reason=form.data["reason"],
                )
                blocked_ip.save()
                messages.success(request, "Cette adresse IP a été bloquée !")
                ip_is_already_blocked = True
                blocked_ips = [blocked_ip]
    else:
        form = BlockedIPForm(is_ipv6_)

    members = Profile.objects.filter(last_ip_address=ip_address).order_by("-last_visit")
    context_data = {
        "members": members,
        "ip": ip_address,
        "is_ipv6": is_ipv6_,
        "ip_location": get_geo_location_from_ip(ip_address),
        "ip_is_already_blocked": ip_is_already_blocked,
        "blocked_ips": blocked_ips,
        "blocked_ip_form": form,
    }

    if is_ipv6_:
        network_ip_filter = get_network_ip_filter(ip_address)
        network_members = Profile.objects.filter(last_ip_address__startswith=network_ip_filter).order_by("-last_visit")
        context_data["network_members"] = network_members
        context_data["network_ip"] = get_network_ip(ip_address)

    return render(request, "member/admin/members_from_ip.html", context_data)
