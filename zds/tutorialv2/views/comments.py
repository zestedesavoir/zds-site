from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from zds import json_handler
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.views import get_client_ip
from zds.notification.models import ContentReactionAnswerSubscription
from zds.tutorialv2.forms import NoteEditForm, NoteForm
from zds.tutorialv2.mixins import MustRedirect, SingleOnlineContentFormViewMixin, SingleOnlineContentViewMixin
from zds.tutorialv2.models.database import ContentReaction
from zds.utils.misc import is_ajax
from zds.utils.models import Alert, CommentEdit, get_hat_from_request


class SendNoteFormView(LoggedWithReadWriteHability, SingleOnlineContentFormViewMixin):
    denied_if_lock = True
    form_class = NoteForm
    check_as = True
    reaction = None
    template_name = "tutorialv2/comment/new.html"

    quoted_reaction_text = ""
    new_note = False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.object
        kwargs["reaction"] = None

        # handle the case when another user have post something in between
        if "last_note" in self.request.POST and self.request.POST["last_note"].strip() != "":
            try:
                last_note = int(self.request.POST["last_note"])
            except ValueError:
                pass
            else:
                if self.object.last_note and last_note != self.object.last_note.pk:
                    self.new_note = True
                    kwargs["last_note"] = self.object.last_note.pk

        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        if self.quoted_reaction_text:
            initial["text"] = self.quoted_reaction_text

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # handle the case were there is a new message in the discussion
        if self.new_note:
            context["newnote"] = True

        # last few messages
        context["notes"] = (
            ContentReaction.objects.select_related("author")
            .select_related("author__profile")
            .select_related("hat")
            .select_related("editor")
            .prefetch_related("alerts_on_this_comment")
            .prefetch_related("alerts_on_this_comment__author")
            .filter(related_content=self.object)
            .order_by("-pubdate")[: settings.ZDS_APP["content"]["notes_per_page"]]
        )

        return context

    def get(self, request, *args, **kwargs):
        # handle quoting case
        if "cite" in self.request.GET:
            try:
                cited_pk = int(self.request.GET["cite"])
            except ValueError:
                raise Http404("L'argument `cite` doit être un entier.")

            reaction = ContentReaction.objects.filter(pk=cited_pk).first()

            if reaction:
                if not reaction.is_visible:
                    raise PermissionDenied

                text = "\n".join("> " + line for line in reaction.text.split("\n"))
                text += f"\nSource: [{reaction.author.username}]({reaction.get_absolute_url()})"

                if is_ajax(self.request):
                    return StreamingHttpResponse(json_handler.dumps({"text": text}, ensure_ascii=False))
                else:
                    self.quoted_reaction_text = text
        try:
            return super().get(request, *args, **kwargs)
        except MustRedirect:
            # if someone changed the pk argument, and reached a 'must redirect' public object
            raise Http404(
                "Aucun contenu public trouvé avec l'identifiant {}".format(str(self.request.GET.get("pk", 0)))
            )

    def post(self, request, *args, **kwargs):
        if "preview" in request.POST and is_ajax(request):
            content = render(request, "misc/preview.part.html", {"text": request.POST["text"]})
            return StreamingHttpResponse(content)
        else:
            return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        if self.check_as and self.object.antispam(self.request.user):
            raise PermissionDenied

        if "preview" in self.request.POST:
            return self.form_invalid(form)

        is_new = False

        if self.reaction:  # it's an edition
            edit = CommentEdit()
            edit.comment = self.reaction
            edit.editor = self.request.user
            edit.original_text = self.reaction.text
            edit.save()

            self.reaction.update = datetime.now()
            self.reaction.editor = self.request.user
            self.reaction.hat = get_hat_from_request(self.request, self.reaction.author)

        else:
            self.reaction = ContentReaction()
            self.reaction.pubdate = datetime.now()
            self.reaction.author = self.request.user
            self.reaction.position = self.object.get_note_count() + 1
            self.reaction.related_content = self.object
            self.reaction.hat = get_hat_from_request(self.request)

            is_new = True

        # also treat alerts if editor is a moderator
        if self.request.user != self.reaction.author and not is_new:
            alerts = Alert.objects.filter(comment__pk=self.reaction.pk, solved=False)
            for alert in alerts:
                alert.solve(self.request.user, _("Le message a été modéré."))

        self.reaction.update_content(
            form.cleaned_data["text"],
            on_error=lambda m: messages.error(self.request, _("Erreur du serveur Markdown: {}").format("\n- ".join(m))),
        )
        self.reaction.ip_address = get_client_ip(self.request)
        self.reaction.save()

        if is_new:  # we first need to save the reaction
            self.object.last_note = self.reaction
            self.object.save(update_date=False)

        self.success_url = self.reaction.get_absolute_url()
        return super().form_valid(form)


class UpdateNoteView(SendNoteFormView):
    check_as = False
    template_name = "tutorialv2/comment/edit.html"
    form_class = NoteEditForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "message" in self.request.GET and self.request.GET["message"].isdigit():
            self.reaction = (
                ContentReaction.objects.prefetch_related("author").filter(pk=int(self.request.GET["message"])).first()
            )
            if not self.reaction:
                raise Http404("Aucun commentaire : " + self.request.GET["message"])
            if self.reaction.author.pk != self.request.user.pk and not self.is_staff:
                raise PermissionDenied()

            kwargs["reaction"] = self.reaction
        else:
            raise Http404("Le paramètre 'message' doit être un nombre entier positif.")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.reaction:
            context["reaction"] = self.reaction

            if self.reaction.author != self.request.user:
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    _(
                        "Vous éditez ce message en tant que modérateur (auteur : {})." " Ne faites pas de bêtise !"
                    ).format(self.reaction.author.username),
                )

                # show alert, if any
                alerts = Alert.objects.filter(comment__pk=self.reaction.pk, solved=False)
                if alerts.count():
                    msg_alert = _(
                        "Attention, en éditant ce message vous résolvez également " "les alertes suivantes : {}"
                    ).format(", ".join([f"« {a.text} » (signalé par {a.author.username})" for a in alerts]))
                    messages.warning(self.request, msg_alert)

        return context

    def form_valid(self, form):
        if "message" in self.request.GET and self.request.GET["message"].isdigit():
            self.reaction = (
                ContentReaction.objects.filter(pk=int(self.request.GET["message"])).prefetch_related("author").first()
            )
            if self.reaction is None:
                raise Http404("Il n'y a aucun commentaire.")
            if self.reaction.author != self.request.user:
                if not self.request.user.has_perm("tutorialv2.change_contentreaction"):
                    raise PermissionDenied
        else:
            messages.error(self.request, _("Oh non ! Une erreur est survenue dans la requête !"))
            return self.form_invalid(form)

        return super().form_valid(form)


class HideReaction(LoginRequiredMixin, FormView):
    http_method_names = ["post"]

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            pk = int(self.kwargs["pk"])
            text = ""
            if "text_hidden" in self.request.POST:
                text = self.request.POST["text_hidden"][:80]  # TODO: Make it less static
            reaction = get_object_or_404(ContentReaction, pk=pk)
            if (
                not self.request.user.has_perm("tutorialv2.change_contentreaction")
                and not self.request.user.pk == reaction.author.pk
            ):
                raise PermissionDenied
            reaction.hide_comment_by_user(self.request.user, text)
            return redirect(reaction.get_absolute_url())
        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404("Vous ne pouvez pas cacher cette réaction.")


class ShowReaction(FormView, LoggedWithReadWriteHability, PermissionRequiredMixin):
    permission_required = "tutorialv2.change_contentreaction"
    http_method_names = ["post"]

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            pk = int(self.kwargs["pk"])
            reaction = get_object_or_404(ContentReaction, pk=pk)
            reaction.is_visible = True
            reaction.save()

            return redirect(reaction.get_absolute_url())

        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404("Aucune réaction trouvée.")


class SendNoteAlert(LoginRequiredMixin, FormView):
    http_method_names = ["post"]

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            reaction_pk = int(self.kwargs["pk"])
        except (KeyError, ValueError):
            raise Http404("Impossible de convertir l'identifiant en entier.")
        reaction = get_object_or_404(ContentReaction, pk=reaction_pk)

        if len(request.POST["signal_text"].strip()) == 0:
            messages.error(request, _("La raison du signalement ne peut pas être vide."))
        else:
            alert = Alert(
                author=request.user,
                comment=reaction,
                scope=reaction.related_content.type,
                text=request.POST["signal_text"],
                pubdate=datetime.now(),
            )
            alert.save()

            messages.success(self.request, _("Ce commentaire a bien été signalé aux modérateurs."))

        return redirect(reaction.get_absolute_url())


class SolveNoteAlert(LoginRequiredMixin, FormView):
    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("tutorialv2.change_contentreaction"):
            raise PermissionDenied
        try:
            alert = get_object_or_404(Alert, pk=int(request.POST["alert_pk"]))
            note = ContentReaction.objects.get(pk=alert.comment.id)
        except (KeyError, ValueError):
            raise Http404("L'alerte n'existe pas.")

        resolve_reason = ""
        msg_title = ""
        msg_content = ""
        if "text" in request.POST and request.POST["text"]:
            resolve_reason = request.POST["text"]
            msg_title = _("Résolution d'alerte : {0}").format(note.related_content.title)
            msg_content = render_to_string(
                "tutorialv2/messages/resolve_alert.md",
                {
                    "content": note.related_content,
                    "url": note.related_content.get_absolute_url_online(),
                    "name": alert.author.username,
                    "target_name": note.author.username,
                    "modo_name": request.user.username,
                    "message": "\n".join(["> " + line for line in resolve_reason.split("\n")]),
                    "alert_text": "\n".join(["> " + line for line in alert.text.split("\n")]),
                },
            )
        alert.solve(request.user, resolve_reason, msg_title, msg_content)

        messages.success(self.request, _("L'alerte a bien été résolue."))
        return redirect(note.get_absolute_url())


class FollowContentReaction(LoggedWithReadWriteHability, SingleOnlineContentViewMixin, FormView):
    redirection_is_needed = False

    def post(self, request, *args, **kwargs):
        response = {}
        self.public_content_object = self.get_public_object()
        if "follow" in request.POST:
            response["follow"] = ContentReactionAnswerSubscription.objects.toggle_follow(
                self.get_object(), self.request.user
            ).is_active
            response["subscriberCount"] = ContentReactionAnswerSubscription.objects.get_subscriptions(
                self.get_object()
            ).count()
        elif "email" in request.POST:
            response["follow"] = ContentReactionAnswerSubscription.objects.toggle_follow(
                self.get_object(), self.request.user, True
            ).is_active
        if is_ajax(self.request):
            return HttpResponse(json_handler.dumps(response), content_type="application/json")
        return redirect(self.get_object().get_absolute_url())
