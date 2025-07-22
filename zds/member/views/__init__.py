from django.conf import settings

from zds.member.models import Profile
from zds.utils.paginator import ZdSPagingListView


class MemberList(ZdSPagingListView):
    """Display the list of registered users."""

    context_object_name = "members"
    paginate_by = settings.ZDS_APP["member"]["members_per_page"]
    template_name = "member/index.html"

    def get_queryset(self):
        self.queryset = Profile.objects.contactable_members()
        return super().get_queryset()
