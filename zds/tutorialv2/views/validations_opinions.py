import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView

from zds.gallery.models import Gallery
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.utils import get_bot_account
from zds.mp.models import filter_reachable
from zds.mp.utils import send_message_mp, send_mp
from zds.tutorialv2 import signals
from zds.tutorialv2.forms import (
    DoNotPickOpinionForm,
    PickOpinionForm,
    PromoteOpinionToArticleForm,
    PublicationForm,
    RevokeValidationForm,
    UnpickOpinionForm,
)
from zds.tutorialv2.mixins import DoesNotRequireValidationFormViewMixin, SingleOnlineContentFormViewMixin
from zds.tutorialv2.models.database import PickListOperation, PublishableContent, Validation
from zds.tutorialv2.publication_utils import FailureDuringPublication, notify_update, publish_content, unpublish_content
from zds.tutorialv2.utils import clone_repo
from zds.tutorialv2.views.validations_contents import logger
from zds.utils.models import get_hat_from_settings


class PublishOpinion(LoggedWithReadWriteHability, DoesNotRequireValidationFormViewMixin):
    """Publish the content (only content without preliminary validation)"""

    form_class = PublicationForm

    modal_form = True
    prefetch_all = False
    must_be_author = True
    authorized_for_staff = True

    def get(self, request, *args, **kwargs):
        raise Http404(_("Publier un contenu n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation
        db_object = self.object
        is_update = bool(db_object.sha_public)
        if self.object.is_permanently_unpublished():
            raise PermissionDenied
        versioned = self.versioned_object
        self.success_url = versioned.get_absolute_url()
        try:
            published = publish_content(db_object, versioned, is_major_update=False)
        except FailureDuringPublication as e:
            messages.error(self.request, e.message)
        else:
            # save in database
            db_object.source = db_object.source
            db_object.sha_validation = None
            db_object.public_version = published
            db_object.save()

            # if only ignore, we remove it from history
            PickListOperation.objects.filter(content=db_object, operation__in=["NO_PICK", "PICK"]).update(
                is_effective=False
            )
            notify_update(db_object, is_update, form.cleaned_data.get("is_major", False))

            signals.opinions_management.send(
                sender=self.__class__, performer=self.request.user, content=self.object, action="publish"
            )
            messages.success(self.request, _("Le contenu a bien été publié."))
            self.success_url = published.get_absolute_url_online()

        return super().form_valid(form)


class UnpublishOpinion(LoginRequiredMixin, SingleOnlineContentFormViewMixin, DoesNotRequireValidationFormViewMixin):
    """Unpublish an opinion"""

    form_class = RevokeValidationForm
    is_public = True

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        versioned = self.versioned_object

        user = self.request.user

        if user not in versioned.authors.all() and not user.has_perm("tutorialv2.change_validation"):
            raise PermissionDenied

        if form.cleaned_data["version"] != self.object.sha_public:
            raise PermissionDenied

        unpublish_content(self.object, moderator=self.request.user)

        if [self.request.user] != list(self.object.authors.all()):
            # Sends PM if the deleter is not the author
            # (or is not the only one) of the opinion.
            msg = render_to_string(
                "tutorialv2/messages/validation_revoke.md",
                {
                    "content": versioned,
                    "url": versioned.get_absolute_url(),
                    "admin": user,
                    "message_reject": "\n".join(["> " + a for a in form.cleaned_data["text"].split("\n")]),
                },
            )

            bot = get_bot_account()
            if self.object.validation_private_message:
                send_message_mp(
                    bot,
                    self.object.validation_private_message,
                    msg,
                    hat=get_hat_from_settings("moderation"),
                    no_notification_for=[self.request.user],
                )
            else:
                recipients = filter_reachable(versioned.authors.all())
                if len(recipients) > 0:
                    self.object.validation_private_message = send_mp(
                        bot,
                        recipients,
                        self.object.validation_message_title,
                        versioned.title,
                        msg,
                        send_by_mail=True,
                        hat=get_hat_from_settings("moderation"),
                    )
                    self.object.save()

        signals.opinions_management.send(
            sender=self.__class__, performer=self.request.user, content=self.object, action="unpublish"
        )

        messages.success(self.request, _("Le contenu a bien été dépublié."))
        self.success_url = self.versioned_object.get_absolute_url()

        return super().form_valid(form)


class DoNotPickOpinion(PermissionRequiredMixin, DoesNotRequireValidationFormViewMixin):
    """Remove"""

    form_class = DoNotPickOpinionForm
    modal_form = False
    prefetch_all = False
    permission_required = "tutorialv2.change_validation"
    template_name = "tutorialv2/validation/opinion-moderation-history.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["operations"] = (
            PickListOperation.objects.filter(content=self.object)
            .order_by("-operation_date")
            .prefetch_related("staff_user", "staff_user__profile")
        )
        return context

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation and validated version
        db_object = self.object
        versioned = self.versioned_object
        self.success_url = versioned.get_absolute_url_online()
        if not db_object.in_public():
            raise Http404("This opinion is not published.")
        elif (
            PickListOperation.objects.filter(content=self.object, is_effective=True).exists()
            and form.cleaned_data["operation"] != "REMOVE_PUB"
        ):
            raise PermissionDenied("There is already an effective operation for this content.")
        try:
            PickListOperation.objects.filter(content=self.object).update(
                is_effective=False, canceler_user=self.request.user
            )
            PickListOperation.objects.create(
                content=self.object,
                operation=form.cleaned_data["operation"],
                staff_user=self.request.user,
                operation_date=datetime.now(),
                version=db_object.sha_public,
            )
            if form.cleaned_data["operation"] == "REMOVE_PUB":
                unpublish_content(self.object, moderator=self.request.user)

                # send PM
                msg = render_to_string(
                    "tutorialv2/messages/validation_unpublish_opinion.md",
                    {
                        "content": versioned,
                        "url": versioned.get_absolute_url(),
                        "moderator": self.request.user,
                    },
                )

                bot = get_bot_account()
                if self.object.validation_private_message:
                    send_message_mp(
                        bot,
                        self.object.validation_private_message,
                        msg,
                        hat=get_hat_from_settings("moderation"),
                        no_notification_for=[self.request.user],
                    )
                else:
                    recipients = filter_reachable(versioned.authors.all())
                    if len(recipients) > 0:
                        self.object.validation_private_message = send_mp(
                            bot,
                            recipients,
                            self.object.validation_message_title,
                            versioned.title,
                            msg,
                            send_by_mail=True,
                            hat=get_hat_from_settings("moderation"),
                        )
                        self.object.save()
        except ValueError:
            logger.exception("Could not %s the opinion %s", form.cleaned_data["operation"], str(self.object))
            return HttpResponse(json.dumps({"result": "FAIL", "reason": str(_("Mauvaise opération"))}), status=400)

        if not form.cleaned_data["redirect"]:
            return HttpResponse(json.dumps({"result": "OK"}))
        else:
            self.success_url = reverse("opinion:list")
            messages.success(self.request, _("Le billet a bien été modéré."))
            return super().form_valid(form)


class RevokePickOperation(PermissionRequiredMixin, FormView):
    """
    Cancel a moderation operation.
    If operation was REMOVE_PUB, it just marks it as canceled, it does
    not republish the opinion.
    """

    form_class = DoNotPickOpinionForm
    prefetch_all = False
    permission_required = "tutorialv2.change_validation"

    def get(self, request, *args, **kwargs):
        raise Http404("Impossible")

    def post(self, request, *args, **kwargs):
        operation = get_object_or_404(PickListOperation, pk=self.kwargs["pk"])
        if not operation.is_effective:
            raise Http404("This operation was already canceled.")
        operation.cancel(self.request.user)
        # if a pick operation is canceled, unpick the content
        if operation.operation == "PICK":
            operation.content.sha_picked = None
            operation.content.save()
        return HttpResponse(json.dumps({"result": "OK"}))


class PickOpinion(PermissionRequiredMixin, DoesNotRequireValidationFormViewMixin):
    """Approve and add an opinion in the picked list."""

    form_class = PickOpinionForm

    modal_form = True
    prefetch_all = False
    permission_required = "tutorialv2.change_validation"

    def get(self, request, *args, **kwargs):
        raise Http404(_("Valider un contenu n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation and validated version
        db_object = self.object
        versioned = self.versioned_object
        self.success_url = versioned.get_absolute_url_online()

        db_object.sha_picked = form.cleaned_data["version"]
        db_object.picked_date = datetime.now()
        db_object.save()

        # mark to reindex to boost correctly in the search
        self.public_content_object.search_engine_requires_index = True
        self.public_content_object.save()
        PickListOperation.objects.create(
            content=self.object,
            operation="PICK",
            staff_user=self.request.user,
            operation_date=datetime.now(),
            version=db_object.sha_picked,
        )
        msg = render_to_string(
            "tutorialv2/messages/validation_opinion.md",
            {
                "title": versioned.title,
                "url": versioned.get_absolute_url(),
            },
        )

        bot = get_bot_account()
        if not self.object.validation_private_message:
            self.object.validation_private_message = send_mp(
                bot,
                versioned.authors.all(),
                self.object.validation_message_title,
                versioned.title,
                msg,
                send_by_mail=True,
                hat=get_hat_from_settings("moderation"),
            )
            self.object.save()
        else:
            send_message_mp(
                bot,
                self.object.validation_private_message,
                msg,
                hat=get_hat_from_settings("moderation"),
                no_notification_for=[self.request.user],
            )

        messages.success(self.request, _("Le billet a bien été choisi."))

        return super().form_valid(form)


class UnpickOpinion(PermissionRequiredMixin, DoesNotRequireValidationFormViewMixin):
    """Remove an opinion from the picked list."""

    form_class = UnpickOpinionForm

    modal_form = True
    prefetch_all = False
    permission_required = "tutorialv2.change_validation"

    def get(self, request, *args, **kwargs):
        raise Http404(_("Enlever un billet des billets choisis n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        db_object = self.object
        versioned = self.versioned_object
        self.success_url = versioned.get_absolute_url_online()

        if not db_object.sha_picked:
            raise PermissionDenied("Impossible de retirer des billets choisis un billet pas choisi.")

        if db_object.sha_picked != form.cleaned_data["version"]:
            raise PermissionDenied("Impossible de retirer des billets choisis un billet pas choisi.")

        db_object.sha_picked = None
        db_object.save()
        PickListOperation.objects.filter(operation="PICK", is_effective=True, content=self.object).first().cancel(
            self.request.user
        )
        # mark to reindex to boost correctly in the search
        self.public_content_object.search_engine_requires_index = True
        self.public_content_object.save()

        msg = render_to_string(
            "tutorialv2/messages/validation_invalid_opinion.md",
            {
                "content": versioned,
                "url": versioned.get_absolute_url(),
                "admin": self.request.user,
                "message_reject": "\n".join(["> " + a for a in form.cleaned_data["text"].split("\n")]),
            },
        )

        bot = get_bot_account()
        if not self.object.validation_private_message:
            self.object.validation_private_message = send_mp(
                bot,
                versioned.authors.all(),
                self.object.validation_message_title,
                versioned.title,
                msg,
                send_by_mail=True,
                hat=get_hat_from_settings("moderation"),
            )
            self.object.save()
        else:
            send_message_mp(bot, self.object.validation_private_message, msg)

        messages.success(self.request, _("Le contenu a bien été enlevé de la liste des billets choisis."))

        return super().form_valid(form)


class ValidationOpinionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List the validations, with possibilities of filters"""

    permission_required = "tutorialv2.change_validation"
    template_name = "tutorialv2/validation/opinions.html"
    context_object_name = "contents"
    subcategory = None

    def get_queryset(self):
        return (
            PublishableContent.objects.filter(type="OPINION", sha_public__isnull=False)
            .exclude(sha_picked=F("sha_public"))
            .exclude(pk__in=PickListOperation.objects.filter(is_effective=True).values_list("content__pk", flat=True))
        )


class PromoteOpinionToArticle(PermissionRequiredMixin, DoesNotRequireValidationFormViewMixin):
    """
    Promote an opinion to an article.
    This duplicates the opinion and declares the clone as an article.
    """

    form_class = PromoteOpinionToArticleForm

    modal_form = True
    prefetch_all = False
    permission_required = "tutorialv2.change_validation"

    def get(self, request, *args, **kwargs):
        raise Http404(_("Promouvoir un billet en article n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation and validated version
        db_object = self.object
        versioned = self.versioned_object

        # get initial git path
        old_git_path = db_object.get_repo_path()

        # store data for later
        authors = db_object.authors.all()
        subcats = db_object.subcategory.all()
        tags = db_object.tags.all()
        article = PublishableContent(
            title=db_object.title,
            type="ARTICLE",
            creation_date=datetime.now(),
            sha_public=db_object.sha_public,
            public_version=None,
            licence=db_object.licence,
            sha_validation=db_object.sha_public,
            sha_draft=db_object.sha_public,
            image=db_object.image,
            source=db_object.source,
        )

        opinion_url = db_object.get_absolute_url_online()
        article.save()
        # add M2M objects
        for author in authors:
            article.authors.add(author)
        for subcat in subcats:
            article.subcategory.add(subcat)
        for tag in tags:
            article.tags.add(tag)
        article.save()
        # add information about the conversion to the original opinion
        db_object.converted_to = article
        db_object.save()

        # clone the repo
        clone_repo(old_git_path, article.get_repo_path())
        versionned_article = article.load_version(sha=article.sha_validation)
        # mandatory to avoid path collision
        versionned_article.slug = article.slug
        article.sha_validation = versionned_article.repo_update(
            versionned_article.title, versionned_article.get_introduction(), versionned_article.get_conclusion()
        )
        article.sha_draft = article.sha_validation
        article.save()
        # ask for validation
        validation = Validation()
        validation.content = article
        validation.date_proposition = datetime.now()
        validation.comment_authors = _(
            "Promotion du billet « [{}]({}) » en article par [{}]({}).".format(
                article.title,
                article.get_absolute_url_online(),
                self.request.user.username,
                self.request.user.profile.get_absolute_url(),
            )
        )
        validation.version = article.sha_validation
        validation.save()
        # creating the gallery
        gal = Gallery()
        gal.title = db_object.gallery.title
        gal.slug = db_object.gallery.slug
        gal.pubdate = datetime.now()
        gal.save()
        article.gallery = gal
        # save updates
        article.save()
        article.ensure_author_gallery()

        # send message to user
        msg = render_to_string(
            "tutorialv2/messages/opinion_promotion.md",
            {
                "content": versioned,
                "url": opinion_url,
            },
        )

        bot = get_bot_account()

        article.validation_private_message = send_mp(
            bot,
            article.authors.all(),
            _("Billet proposé comme article"),
            versionned_article.title,
            msg,
            send_by_mail=True,
            hat=get_hat_from_settings("validation"),
        )
        article.save()

        self.success_url = db_object.get_absolute_url()

        messages.success(
            self.request,
            _(
                """Le billet a bien été copié sous forme d’article
                                            et est en attente de validation."""
            ),
        )

        return super().form_valid(form)
