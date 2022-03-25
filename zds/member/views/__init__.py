from django.conf import settings

from zds.member.models import Profile
from zds.utils.paginator import ZdSPagingListView


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


class MemberList(ZdSPagingListView):
    """Display the list of registered users."""

    context_object_name = "members"
    paginate_by = settings.ZDS_APP["member"]["members_per_page"]
    template_name = "member/index.html"

    def get_queryset(self):
        self.queryset = Profile.objects.contactable_members()
        return super().get_queryset()
