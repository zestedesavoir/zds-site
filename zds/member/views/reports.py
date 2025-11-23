from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from zds.member.decorator import LoginRequiredMixin
from zds.member.models import Profile
from zds.utils.models import Alert


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
