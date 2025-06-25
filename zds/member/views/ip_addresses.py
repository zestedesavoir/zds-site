from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin

from zds.member.decorator import LoginRequiredMixin
from zds.member.models import BlockedIP
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
