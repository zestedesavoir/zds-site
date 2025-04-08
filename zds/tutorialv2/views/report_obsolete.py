from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from zds.tutorialv2.forms import DecideObsoleteForm
from zds.tutorialv2.models.database import PotentialObsolete
from zds.utils.paginator import ZdSPagingListView


class PotentialObsoleteContentListView(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    """
    Displays a paginated list of reports of potential obsolete contents.
    Only accessible to staff members.
    """

    permission_required = "tutorialv2.change_publishablecontent"
    model = PotentialObsolete
    template_name = "tutorialv2/list_page_elements/potentialobsolete_list.html"
    context_object_name = "reports"
    ordering = "-report_date"
    paginate_by = 10

    def get_queryset(self):
        """Customize the queryset to order by report_date (most recent first)."""
        return PotentialObsolete.objects.all().select_related("publishable_content").order_by(self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forms_decide_obsolete"] = {report.pk: DecideObsoleteForm(obj=report) for report in context["reports"]}
        return context
