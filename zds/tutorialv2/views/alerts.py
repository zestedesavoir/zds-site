from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from zds.tutorialv2.models.database import PublishableContent
from zds.utils.models import Alert


class SendContentAlert(LoginRequiredMixin, FormView):
    http_method_names = ["post"]

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            content_pk = int(self.kwargs["pk"])
        except (KeyError, ValueError):
            raise Http404(_("Identifiant manquant ou conversion en entier impossible."))

        content = get_object_or_404(PublishableContent, pk=content_pk)

        if content.type != "OPINION":
            raise Http404(_("Il n'est possible de signaler que des billets."))

        if not content.in_public():
            raise Http404(_("Ce billet n'a pas (plus ?) de version publique."))

        if len(request.POST["signal_text"].strip()) == 0:
            messages.error(request, _("La raison du signalement ne peut pas être vide."))
        else:
            alert = Alert(
                author=request.user,
                content=content,
                scope="CONTENT",
                text=request.POST["signal_text"],
                pubdate=datetime.now(),
            )
            alert.save()

            messages.success(self.request, _("Ce billet a bien été signalé aux modérateurs."))

        return redirect(content.get_absolute_url_online())


class SolveContentAlert(LoginRequiredMixin, FormView):
    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Note: a specific permission would be better.
        if not request.user.has_perm("tutorialv2.change_contentreaction"):
            raise PermissionDenied
        try:
            alert = get_object_or_404(Alert, pk=int(request.POST["alert_pk"]))
        except (KeyError, ValueError):
            raise Http404("L'alerte n'existe pas.")

        if alert.scope != "CONTENT":
            raise Http404(_("L'alerte ne concerne pas un contenu."))

        content = get_object_or_404(PublishableContent, pk=alert.content.id)

        if alert.solved:
            raise Http404("L'alerte a déjà été résolue.")

        resolve_reason = ""
        msg_title = ""
        msg_content = ""
        if "text" in request.POST and request.POST["text"]:
            resolve_reason = request.POST["text"]
            authors = alert.content.authors.values_list("username", flat=True)
            authors = ", ".join(authors)
            msg_title = _("Résolution d'alerte : {0}").format(content.title)
            msg_content = render_to_string(
                "tutorialv2/messages/resolve_alert.md",
                {
                    "content": content,
                    "url": content.get_absolute_url_online(),
                    "name": alert.author.username,
                    "target_name": authors,
                    "modo_name": request.user.username,
                    "message": "\n".join(["> " + line for line in resolve_reason.split("\n")]),
                    "alert_text": "\n".join(["> " + line for line in alert.text.split("\n")]),
                },
            )
        alert.solve(request.user, resolve_reason, msg_title, msg_content)

        messages.success(self.request, _("L'alerte a bien été résolue."))
        return redirect(content.get_absolute_url_online())
