from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from zds.member.decorator import LoginRequiredMixin
from zds.member.models import Profile
from zds.tutorialv2.forms import DecideObsoleteForm
from zds.tutorialv2.models.database import PotentialObsolete
from zds.utils.models import Alert
from zds.utils.paginator import ZdSPagingListView


class CreateProfileReportView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, pk=kwargs["profile_pk"])
        reason = request.POST.get("reason", "")
        if reason == "":
            messages.warning(request, _("Veuillez saisir une raison."))
        else:
            alert = Alert(author=request.user, profile=profile, scope="PROFILE", text=reason, pubdate=datetime.now())
            alert.save()
            messages.success(
                request, _("Votre signalement a été transmis à l'équipe de modération. " "Merci de votre aide !")
            )
        return redirect(profile.get_absolute_url())


class SolveProfileReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "member.change_profile"

    def post(self, request, *args, **kwargs):
        alert = get_object_or_404(Alert, pk=kwargs["alert_pk"], solved=False, scope="PROFILE")
        text = request.POST.get("text", "")
        if text:
            msg_title = _("Signalement traité : profil de {}").format(alert.profile.user.username)
            msg_content = render_to_string(
                "member/messages/alert_solved.md",
                {
                    "alert_author": alert.author.username,
                    "reported_user": alert.profile.user.username,
                    "moderator": request.user.username,
                    "staff_message": text,
                },
            )
            alert.solve(request.user, text, msg_title, msg_content)
        else:
            alert.solve(request.user)
        messages.success(request, _("Merci, l'alerte a bien été résolue."))
        return redirect(alert.profile.get_absolute_url())


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
        return PotentialObsolete.objects.all().select_related("published_content").order_by(self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forms_decide_obsolete"] = {report.pk: DecideObsoleteForm(obj=report) for report in context["reports"]}
        return context
