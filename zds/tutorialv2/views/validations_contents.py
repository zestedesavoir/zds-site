import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, FormView

from zds.member.decorator import LoginRequiredMixin, PermissionRequiredMixin, LoggedWithReadWriteHability
from zds.mp.models import mark_read
from zds.tutorialv2.forms import (
    AskValidationForm,
    RejectValidationForm,
    AcceptValidationForm,
    RevokeValidationForm,
    CancelValidationForm,
    JsFiddleActivationForm,
)
from zds.tutorialv2.mixins import (
    SingleContentFormViewMixin,
    ModalFormView,
    SingleOnlineContentFormViewMixin,
    RequiresValidationViewMixin,
)
from zds.tutorialv2.models.database import Validation, PublishableContent
from zds.tutorialv2.publication_utils import (
    publish_content,
    unpublish_content,
    notify_update,
    FailureDuringPublication,
    save_validation_state,
)
from zds.utils.models import SubCategory, get_hat_from_settings
from zds.utils.mps import send_mp, send_message_mp

logger = logging.getLogger(__name__)


class ValidationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List the validations, with possibilities of filters"""

    permissions = ["tutorialv2.change_validation"]
    context_object_name = "validations"
    template_name = "tutorialv2/validation/index.html"
    subcategory = None

    def get_queryset(self):

        # TODO: many filter at the same time ?
        # TODO: paginate ?

        queryset = (
            Validation.objects.prefetch_related("validator")
            .prefetch_related("content")
            .prefetch_related("content__authors")
            .prefetch_related("content__subcategory")
            .filter(Q(status="PENDING") | Q(status="PENDING_V"))
        )

        # filtering by type
        try:
            type_ = self.request.GET["type"]
            if type_ == "orphan":
                queryset = queryset.filter(validator__isnull=True, status="PENDING")
            if type_ == "reserved":
                queryset = queryset.filter(validator__isnull=False, status="PENDING_V")
            if type_ == "article":
                queryset = queryset.filter(content__type="ARTICLE")
            if type_ == "tuto":
                queryset = queryset.filter(content__type="TUTORIAL")
            else:
                raise KeyError()
        except KeyError:
            pass

        # filtering by category
        try:
            category_pk = int(self.request.GET["subcategory"])
            self.subcategory = get_object_or_404(SubCategory, pk=category_pk)
            queryset = queryset.filter(content__subcategory__in=[self.subcategory])
        except KeyError:
            pass
        except ValueError:
            raise Http404("Format invalide pour le paramètre de la sous-catégorie.")

        return queryset.order_by("date_proposition").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        removed_ids = []
        for validation in context["validations"]:
            try:
                validation.versioned_content = validation.content.load_version(sha=validation.content.sha_validation)
            except OSError:  # remember that load_version can raise OSError when path is not correct
                logger.warning(f"A validation {validation.pk} for content {validation.content.title} failed to load")
                removed_ids.append(validation.pk)
        context["validations"] = [_valid for _valid in context["validations"] if _valid.pk not in removed_ids]
        context["category"] = self.subcategory
        return context


class AskValidationForContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """
    Request validation for a tutorial.
    Can be used by regular users or staff.
    """

    prefetch_all = False
    form_class = AskValidationForm
    must_be_author = True
    authorized_for_staff = True  # an admin could ask validation for a content
    only_draft_version = False
    modal_form = True

    def get_form_kwargs(self):
        if not self.versioned_object.requires_validation():
            raise PermissionDenied
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):

        old_validation = Validation.objects.filter(
            content__pk=self.object.pk, status__in=["PENDING", "PENDING_V"]
        ).first()

        if old_validation:  # if an old validation exists, cancel it!
            old_validator = old_validation.validator
            old_validation.status = "CANCEL"
            old_validation.date_validation = datetime.now()
            old_validation.save()
        else:
            old_validator = None

        # create a 'validation' object
        validation = Validation()
        validation.content = self.object
        validation.date_proposition = datetime.now()
        validation.comment_authors = form.cleaned_data["text"]
        validation.version = form.cleaned_data["version"]
        if old_validator:
            validation.validator = old_validator
            validation.date_reserve = old_validation.date_reserve
            validation.status = "PENDING_V"
        validation.save()

        # warn the former validator that an update has been made, if any
        if old_validator:
            bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
            msg = render_to_string(
                "tutorialv2/messages/validation_change.md",
                {
                    "content": self.versioned_object,
                    "validator": validation.validator.username,
                    "url": self.versioned_object.get_absolute_url() + "?version=" + form.cleaned_data["version"],
                    "url_history": reverse("content:history", args=[self.object.pk, self.object.slug]),
                },
            )
            if not self.object.validation_private_message:
                self.object.validation_private_message = send_mp(
                    bot,
                    [old_validator],
                    self.object.validation_message_title,
                    self.versioned_object.title,
                    msg,
                    send_by_mail=False,
                    hat=get_hat_from_settings("validation"),
                )
            else:
                send_message_mp(bot, self.object.validation_private_message, msg)

        # update the content with the source and the version of the validation
        self.object.source = self.versioned_object.source
        self.object.sha_validation = validation.version
        self.object.save()

        messages.success(self.request, _("Votre demande de validation a été transmise à l'équipe."))

        self.success_url = self.versioned_object.get_absolute_url(version=self.sha)
        return super().form_valid(form)


class CancelValidation(LoginRequiredMixin, ModalFormView):
    """
    Cancel the validation process.
    Can be used by regular users or staff.
    """

    form_class = CancelValidationForm

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["validation"] = Validation.objects.filter(pk=self.kwargs["pk"]).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user

        validation = (
            Validation.objects.filter(pk=self.kwargs["pk"])
            .prefetch_related("content")
            .prefetch_related("content__authors")
            .last()
        )

        if not validation:
            raise PermissionDenied

        if validation.status not in ["PENDING", "PENDING_V"]:
            raise PermissionDenied  # cannot cancel a validation that is already accepted or rejected

        if user not in validation.content.authors.all() and not user.has_perm("tutorialv2.change_validation"):
            raise PermissionDenied

        versioned = validation.content.load_version(sha=validation.version)

        # reject validation:
        quote = "\n".join(["> " + line for line in form.cleaned_data["text"].split("\n")])
        validation.status = "CANCEL"
        validation.comment_authors = _("\n\nLa validation a été **annulée** pour la raison suivante :\n\n{}").format(
            quote
        )
        validation.date_validation = datetime.now()
        validation.save()

        validation.content.sha_validation = None
        validation.content.save()

        # warn the former validator that the whole thing has been cancelled
        if validation.validator:
            bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
            msg = render_to_string(
                "tutorialv2/messages/validation_cancel.md",
                {
                    "content": versioned,
                    "validator": validation.validator.username,
                    "url": versioned.get_absolute_url() + "?version=" + validation.version,
                    "user": self.request.user,
                    "message": quote,
                },
            )
            if not validation.content.validation_private_message:
                validation.content.validation_private_message = send_mp(
                    bot,
                    [validation.validator],
                    _("Demande de validation annulée").format(),
                    versioned.title,
                    msg,
                    send_by_mail=False,
                    hat=get_hat_from_settings("validation"),
                )
                validation.content.save()
            else:
                send_message_mp(bot, validation.content.validation_private_message, msg)

        messages.info(self.request, _("La validation de ce contenu a bien été annulée."))

        self.success_url = (
            reverse("content:view", args=[validation.content.pk, validation.content.slug])
            + "?version="
            + validation.version
        )

        return super().form_valid(form)


class ReserveValidation(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Reserve or remove the reservation on a content"""

    permissions = ["tutorialv2.change_validation"]

    def post(self, request, *args, **kwargs):
        validation = get_object_or_404(Validation, pk=kwargs["pk"])
        if validation.validator:
            validation.validator = None
            validation.date_reserve = None
            validation.status = "PENDING"
            validation.save()
            messages.info(request, _("Ce contenu n'est plus réservé."))
            return redirect(reverse("validation:list"))
        else:
            validation.validator = request.user
            validation.date_reserve = datetime.now()
            validation.status = "PENDING_V"
            validation.save()

            versioned = validation.content.load_version(sha=validation.version)
            msg = render_to_string(
                "tutorialv2/messages/validation_reserve.md",
                {
                    "content": versioned,
                    "url": versioned.get_absolute_url() + "?version=" + validation.version,
                },
            )

            authors = list(validation.content.authors.all())
            if validation.validator in authors:
                authors.remove(validation.validator)
            if len(authors) > 0:
                if not validation.content.validation_private_message:
                    validation.content.validation_private_message = send_mp(
                        validation.validator,
                        authors,
                        _("Contenu réservé - {0}").format(validation.content.title),
                        validation.content.title,
                        msg,
                        send_by_mail=True,
                        leave=False,
                        direct=False,
                        mark_as_read=True,
                        hat=get_hat_from_settings("validation"),
                    )
                    validation.content.save()
                else:
                    send_message_mp(validation.validator, validation.content.validation_private_message, msg)
                mark_read(validation.content.validation_private_message, validation.validator)

            messages.info(request, _("Ce contenu a bien été réservé par {0}.").format(request.user.username))

            return redirect(
                reverse("content:view", args=[validation.content.pk, validation.content.slug])
                + "?version="
                + validation.version
            )


class ValidationHistoryView(LoginRequiredMixin, PermissionRequiredMixin, RequiresValidationViewMixin):

    model = PublishableContent
    permissions = ["tutorialv2.change_validation"]
    template_name = "tutorialv2/validation/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context["validations"] = (
            Validation.objects.prefetch_related("validator")
            .filter(content__pk=self.object.pk)
            .order_by("date_proposition")
            .all()
        )

        return context


class RejectValidation(LoginRequiredMixin, PermissionRequiredMixin, ModalFormView):
    """Reject the publication"""

    permissions = ["tutorialv2.change_validation"]
    form_class = RejectValidationForm

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["validation"] = Validation.objects.filter(pk=self.kwargs["pk"]).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user

        validation = Validation.objects.filter(pk=self.kwargs["pk"]).last()

        if not validation:
            raise PermissionDenied

        if validation.validator != user:
            raise PermissionDenied

        if validation.status != "PENDING_V":
            raise PermissionDenied

        # reject validation:
        validation.comment_validator = form.cleaned_data["text"]
        validation.status = "REJECT"
        validation.date_validation = datetime.now()
        validation.save()

        validation.content.sha_validation = None
        validation.content.save()

        # send PM
        versioned = validation.content.load_version(sha=validation.version)
        msg = render_to_string(
            "tutorialv2/messages/validation_reject.md",
            {
                "content": versioned,
                "url": versioned.get_absolute_url() + "?version=" + validation.version,
                "validator": validation.validator,
                "message_reject": "\n".join(["> " + a for a in form.cleaned_data["text"].split("\n")]),
            },
        )

        bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
        if not validation.content.validation_private_message:
            validation.content.validation_private_message = send_mp(
                bot,
                validation.content.authors.all(),
                _("Rejet de la demande de publication").format(),
                validation.content.title,
                msg,
                send_by_mail=True,
                direct=False,
                hat=get_hat_from_settings("validation"),
            )
            validation.content.save()
        else:
            send_message_mp(
                bot, validation.content.validation_private_message, msg, no_notification_for=[self.request.user]
            )

        messages.info(self.request, _("Le contenu a bien été refusé."))
        self.success_url = reverse("validation:list")
        return super().form_valid(form)


class AcceptValidation(LoginRequiredMixin, PermissionRequiredMixin, ModalFormView):
    """Publish the content"""

    permissions = ["tutorialv2.change_validation"]
    form_class = AcceptValidationForm

    modal_form = True

    def get(self, request, *args, **kwargs):
        raise Http404("Publier un contenu depuis la validation n'est pas disponible en GET.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["validation"] = Validation.objects.filter(pk=self.kwargs["pk"]).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user
        validation = Validation.objects.filter(pk=self.kwargs["pk"]).last()

        if not validation:
            raise PermissionDenied

        if validation.validator != user:
            raise PermissionDenied

        if validation.status != "PENDING_V":
            raise PermissionDenied

        # get database representation and validated version
        db_object = validation.content
        versioned = db_object.load_version(sha=validation.version)
        self.success_url = versioned.get_absolute_url(version=validation.version)
        is_update = db_object.sha_public
        try:
            published = publish_content(db_object, versioned, is_major_update=form.cleaned_data["is_major"])
        except FailureDuringPublication as e:
            messages.error(self.request, e.message)
        else:
            save_validation_state(
                db_object,
                is_update,
                published,
                validation,
                versioned,
                source=db_object.source,
                is_major=form.cleaned_data["is_major"],
                user=self.request.user,
                request=self.request,
                comment=form.cleaned_data["text"],
            )
            notify_update(db_object, is_update, form.cleaned_data["is_major"])

            messages.success(self.request, _("Le contenu a bien été validé."))
            self.success_url = published.get_absolute_url_online()

        return super().form_valid(form)


class RevokeValidation(LoginRequiredMixin, PermissionRequiredMixin, SingleOnlineContentFormViewMixin):
    """Unpublish a content and reverse the situation back to a pending validation"""

    permissions = ["tutorialv2.change_validation"]
    form_class = RevokeValidationForm
    is_public = True

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):

        versioned = self.versioned_object

        if form.cleaned_data["version"] != self.object.sha_public:
            raise PermissionDenied

        validation = (
            Validation.objects.filter(content=self.object, version=self.object.sha_public, status="ACCEPT")
            .prefetch_related("content__authors")
            .last()
        )

        if not validation:
            raise PermissionDenied

        unpublish_content(self.object)

        validation.status = "PENDING"
        validation.validator = None  # remove previous validator
        validation.date_validation = None
        validation.save()

        self.object.sha_public = None
        self.object.sha_validation = validation.version
        self.object.pubdate = None
        self.object.save()

        # send PM
        msg = render_to_string(
            "tutorialv2/messages/validation_revoke.md",
            {
                "content": versioned,
                "url": versioned.get_absolute_url() + "?version=" + validation.version,
                "admin": self.request.user,
                "message_reject": "\n".join(["> " + a for a in form.cleaned_data["text"].split("\n")]),
            },
        )

        bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
        if not validation.content.validation_private_message:
            validation.content.validation_private_message = send_mp(
                bot,
                validation.content.authors.all(),
                self.object.validation_message_title,
                validation.content.title,
                msg,
                send_by_mail=True,
                direct=False,
                hat=get_hat_from_settings("validation"),
            )
            self.object.save()
        else:
            send_message_mp(
                bot, validation.content.validation_private_message, msg, no_notification_for=[self.request.user]
            )

        messages.success(self.request, _("Le contenu a bien été dépublié."))
        self.success_url = self.versioned_object.get_absolute_url() + "?version=" + validation.version

        return super().form_valid(form)


class MarkObsolete(LoginRequiredMixin, PermissionRequiredMixin, FormView):

    permissions = ["tutorialv2.change_validation"]

    def get(self, request, *args, **kwargs):
        raise Http404("Marquer un contenu comme obsolète n'est pas disponible en GET.")

    def post(self, request, *args, **kwargs):
        content = get_object_or_404(PublishableContent, pk=kwargs["pk"])
        if not content.in_public():
            raise Http404
        if content.is_obsolete:
            content.is_obsolete = False
            messages.info(request, _("Le contenu n'est plus marqué comme obsolète."))
        else:
            content.is_obsolete = True
            messages.info(request, _("Le contenu est maintenant marqué comme obsolète."))
        content.save()
        return redirect(content.get_absolute_url_online())


class ActivateJSFiddleInContent(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Handles changes a validator or staff member can do on the js fiddle support of the provided content
    Only these users can do it"""

    permissions = ["tutorialv2.change_publishablecontent"]
    form_class = JsFiddleActivationForm
    http_method_names = ["post"]

    def form_valid(self, form):
        """Change the js fiddle support of content and redirect to the view page"""

        content = get_object_or_404(PublishableContent, pk=form.cleaned_data["pk"])
        # forbidden for content without a validation before publication
        if not content.load_version().requires_validation():
            raise PermissionDenied
        content.update(js_support=form.cleaned_data["js_support"])
        return redirect(content.load_version().get_absolute_url())
