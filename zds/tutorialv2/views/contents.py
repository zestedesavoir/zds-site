import logging
from datetime import datetime

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms import forms, CharField
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from zds.gallery.mixins import ImageCreateMixin, NotAnImage
from zds.gallery.models import Gallery
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.utils import get_bot_account
from zds.tutorialv2.forms import (
    ContentForm,
    FormWithTitle,
    EditContentForm,
)
from zds.tutorialv2.mixins import (
    SingleContentFormViewMixin,
    SingleContentViewMixin,
    FormWithPreview,
)
from zds.tutorialv2.models.database import PublishableContent, Validation
from zds.tutorialv2.utils import init_new_repo
from zds.tutorialv2.views.authors import RemoveAuthorFromContent
from zds.utils.models import get_hat_from_settings
from zds.mp.utils import send_mp, send_message_mp
from zds.utils.uuslug_wrapper import slugify
from zds.tutorialv2.models import CONTENT_TYPE_LIST

logger = logging.getLogger(__name__)


class CreateContent(LoggedWithReadWriteHability, FormWithPreview):
    """
    Handle content creation. Since v22 a licence must be explicitly selected
    instead of defaulting to "All rights reserved". Users can however
    set a default licence in their profile.
    """

    template_name = "tutorialv2/create/content.html"
    model = PublishableContent
    form_class = ContentForm
    content = None
    created_content_type = "TUTORIAL"

    def get_form(self, form_class=ContentForm):
        form = super().get_form(form_class)
        content_type = self.kwargs["created_content_type"]
        if content_type in CONTENT_TYPE_LIST:
            self.created_content_type = content_type
        form.initial["type"] = self.created_content_type
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editorial_line_link"] = settings.ZDS_APP["content"]["editorial_line_link"]
        context["site_name"] = settings.ZDS_APP["site"]["literal_name"]
        return context

    def form_valid(self, form):
        # create the object:
        self.content = PublishableContent()
        self.content.title = form.cleaned_data["title"]
        self.content.description = form.cleaned_data["description"]
        self.content.type = form.cleaned_data["type"]
        self.content.licence = self.request.user.profile.licence  # Use the preferred license of the user if it exists
        self.content.source = form.cleaned_data["source"]
        self.content.creation_date = datetime.now()

        gallery = Gallery.objects.create(
            title=self.content.title,
            slug=slugify(self.content.title),
            pubdate=datetime.now(),
        )

        # create image:
        if "image" in self.request.FILES:
            mixin = ImageCreateMixin()
            mixin.gallery = gallery
            try:
                img = mixin.perform_create(str(_("Icône du contenu")), self.request.FILES["image"])
            except NotAnImage:
                form.add_error("image", _("Image invalide"))
                return super().form_invalid(form)
            img.pubdate = datetime.now()
        self.content.gallery = gallery
        self.content.save()
        if "image" in self.request.FILES:
            self.content.image = img
            self.content.save()

        # We need to save the content before changing its author list since it's a many-to-many relationship
        self.content.authors.add(self.request.user)

        self.content.ensure_author_gallery()
        self.content.save()
        # Add subcategories on tutorial
        for subcat in form.cleaned_data["subcategory"]:
            self.content.subcategory.add(subcat)

        self.content.save()

        # create a new repo :
        init_new_repo(
            self.content,
            form.cleaned_data["introduction"],
            form.cleaned_data["conclusion"],
            form.cleaned_data["msg_commit"],
        )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("content:view", args=[self.content.pk, self.content.slug])


class EditContent(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = "tutorialv2/edit/content.html"
    model = PublishableContent
    form_class = EditContentForm

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super().get_initial()
        versioned = self.versioned_object

        initial["introduction"] = versioned.get_introduction()
        initial["conclusion"] = versioned.get_conclusion()
        initial["source"] = versioned.source
        initial["subcategory"] = self.object.subcategory.all()
        initial["last_hash"] = versioned.compute_hash()

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "preview" not in self.request.POST:
            context["gallery"] = self.object.gallery

        return context

    def form_valid(self, form):
        versioned = self.versioned_object
        publishable = self.object

        # check if content has changed:
        current_hash = versioned.compute_hash()
        if current_hash != form.cleaned_data["last_hash"]:
            data = form.data.copy()
            data["last_hash"] = current_hash
            data["introduction"] = versioned.get_introduction()
            data["conclusion"] = versioned.get_conclusion()
            form.data = data
            messages.error(self.request, _("Une nouvelle version a été postée avant que vous ne validiez."))
            return self.form_invalid(form)

        # Forbid removing all categories of a validated content
        if publishable.in_public() and not form.cleaned_data["subcategory"]:
            messages.error(
                self.request, _("Vous devez choisir au moins une catégorie, car ce contenu est déjà publié.")
            )
            return self.form_invalid(form)

        # first, update DB (in order to get a new slug if needed)
        publishable.source = form.cleaned_data["source"]

        publishable.update_date = datetime.now()

        # update image
        if "image" in self.request.FILES:
            gallery_defaults = {
                "title": publishable.title,
                "slug": slugify(publishable.title),
                "pubdate": datetime.now(),
            }
            gallery, _ = Gallery.objects.get_or_create(pk=publishable.gallery.pk, defaults=gallery_defaults)
            mixin = ImageCreateMixin()
            mixin.gallery = gallery
            try:
                img = mixin.perform_create(str(_("Icône du contenu")), self.request.FILES["image"])
            except NotAnImage:
                form.add_error("image", _("Image invalide"))
                return super().form_invalid(form)
            img.pubdate = datetime.now()
            publishable.image = img

        publishable.save()

        # now, update the versioned information
        sha = versioned.repo_update_top_container(
            publishable.title,
            publishable.slug,
            form.cleaned_data["introduction"],
            form.cleaned_data["conclusion"],
            form.cleaned_data["msg_commit"],
        )

        # update relationships :
        publishable.sha_draft = sha

        publishable.subcategory.clear()
        for subcat in form.cleaned_data["subcategory"]:
            publishable.subcategory.add(subcat)

        publishable.save()

        self.success_url = reverse("content:view", args=[publishable.pk, publishable.slug])
        return super().form_valid(form)


class EditTitleForm(FormWithTitle):
    def __init__(self, versioned_content, *args, **kwargs):
        kwargs["initial"] = {"title": versioned_content.title}
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_id = "edit-title"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_action = reverse("content:edit-title", kwargs={"pk": versioned_content.pk})
        self.helper.layout = Layout(
            Field("title"),
            StrictButton("Modifier", type="submit"),
        )
        self.previous_page_url = reverse(
            "content:view", kwargs={"pk": versioned_content.pk, "slug": versioned_content.slug}
        )


class EditTitle(LoginRequiredMixin, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditTitleForm
    success_message = _("Le titre de la publication a bien été changé.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["versioned_content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object
        versioned = self.versioned_object
        title = form.cleaned_data["title"]

        self.update_title_in_database(publishable, title)
        logger.debug("content %s updated, slug is %s", publishable.pk, publishable.slug)

        sha = self.update_title_in_repository(publishable, versioned, title)
        logger.debug("slug consistency after repo update repo=%s db=%s", versioned.slug, publishable.slug)

        self.update_gallery(publishable)
        self.update_sha_draft(publishable, sha)

        messages.success(self.request, self.success_message)

        # A title update usually also changes the slug
        form.previous_page_url = reverse("content:view", kwargs={"pk": versioned.pk, "slug": versioned.slug})

        return redirect(form.previous_page_url)

    @staticmethod
    def update_title_in_database(publishable_content, title):
        title_has_changed = publishable_content.title != title
        publishable_content.title = title
        publishable_content.save(force_slug_update=title_has_changed, force_update=True)

    @staticmethod
    def update_title_in_repository(publishable_content, versioned_content, title):
        versioned_content.title = title
        sha = versioned_content.repo_update_top_container(
            publishable_content.title,
            publishable_content.slug,
            versioned_content.get_introduction(),
            versioned_content.get_conclusion(),
            f"Nouveau titre ({title})",
        )
        return sha

    @staticmethod
    def update_sha_draft(publishable_content, sha):
        publishable_content.sha_draft = sha
        publishable_content.save()

    @staticmethod
    def update_gallery(publishable_content):
        gallery = Gallery.objects.filter(pk=publishable_content.gallery.pk).first()
        gallery.title = publishable_content.title
        gallery.slug = slugify(publishable_content.title)
        gallery.update = datetime.now()
        gallery.save()


class EditSubtitleForm(forms.Form):
    subtitle = CharField(
        label=_("Sous-titre"),
        max_length=PublishableContent._meta.get_field("description").max_length,
        required=False,
    )

    def __init__(self, versioned_content, *args, **kwargs):
        kwargs["initial"] = {"subtitle": versioned_content.description}
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_id = "edit-subtitle"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_action = reverse("content:edit-subtitle", kwargs={"pk": versioned_content.pk})
        self.helper.layout = Layout(
            Field("subtitle"),
            StrictButton("Modifier", type="submit"),
        )
        self.previous_page_url = reverse(
            "content:view", kwargs={"pk": versioned_content.pk, "slug": versioned_content.slug}
        )


class EditSubtitle(LoginRequiredMixin, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditSubtitleForm
    success_message = _("Le sous-titre de la publication a bien été changé.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["versioned_content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object
        versioned = self.versioned_object

        self.update_subtitle_in_database(publishable, form.cleaned_data["subtitle"])
        sha = self.update_subtitle_in_repository(publishable, versioned, form.cleaned_data["subtitle"])
        self.update_sha_draft(publishable, sha)

        messages.success(self.request, self.success_message)

        return redirect(form.previous_page_url)

    @staticmethod
    def update_subtitle_in_database(publishable_content, subtitle):
        publishable_content.description = subtitle
        publishable_content.save(force_update=True)

    @staticmethod
    def update_subtitle_in_repository(publishable_content, versioned_content, subtitle):
        versioned_content.description = subtitle
        sha = versioned_content.repo_update_top_container(
            publishable_content.title,
            publishable_content.slug,
            versioned_content.get_introduction(),
            versioned_content.get_conclusion(),
            f"Nouveau sous-titre ({subtitle})",
        )
        return sha

    @staticmethod
    def update_sha_draft(publishable_content, sha):
        publishable_content.sha_draft = sha
        publishable_content.save()


class DeleteContent(LoginRequiredMixin, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    http_method_names = ["post"]
    authorized_for_staff = False  # deletion is creator's privilege

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = self.get_object()
        object_type = self.object.type.lower()

        _type = _("ce tutoriel")
        if self.object.is_article:
            _type = _("cet article")
        elif self.object.is_opinion:
            _type = _("ce billet")

        if self.object.authors.count() > 1:  # if more than one author, just remove author from list
            RemoveAuthorFromContent.remove_author(self.object, self.request.user)
            messages.success(self.request, _("Vous avez quitté la rédaction de {}.").format(_type))

        else:
            validation = Validation.objects.filter(content=self.object).order_by("-date_proposition").first()

            if validation and validation.status == "PENDING_V":  # if the validation have a validator, warn him by PM
                if "text" not in self.request.POST or len(self.request.POST["text"].strip()) < 3:
                    messages.error(self.request, _("Merci de fournir une raison à la suppression."))
                    return redirect(self.object.get_absolute_url())
                else:
                    bot = get_bot_account()
                    msg = render_to_string(
                        "tutorialv2/messages/validation_cancel_on_delete.md",
                        {
                            "content": self.object,
                            "validator": validation.validator.username,
                            "user": self.request.user,
                            "message": "\n".join(["> " + line for line in self.request.POST["text"].split("\n")]),
                        },
                    )
                    if not validation.content.validation_private_message:
                        validation.content.validation_private_message = send_mp(
                            bot,
                            [validation.validator],
                            _("Demande de validation annulée").format(),
                            self.object.title,
                            msg,
                            send_by_mail=False,
                            leave=True,
                            hat=get_hat_from_settings("validation"),
                            automatically_read=validation.validator,
                        )
                        validation.content.save()
                    else:
                        send_message_mp(
                            bot,
                            validation.content.validation_private_message,
                            msg,
                            hat=get_hat_from_settings("validation"),
                            no_notification_for=[self.request.user],
                        )
            if self.object.beta_topic is not None:
                beta_topic = self.object.beta_topic
                beta_topic.is_locked = True
                beta_topic.add_tags(["Supprimé"])
                beta_topic.save()
                post = beta_topic.first_post()
                post.update_content(
                    _("[[a]]\n" "| Malheureusement, {} qui était en bêta a été supprimé par son auteur.\n\n").format(
                        _type
                    )
                    + post.text
                )

                post.save()

            self.object.delete()

            messages.success(self.request, _("Vous avez bien supprimé {}.").format(_type))

        return redirect(reverse(object_type + ":find-" + object_type, args=[self.request.user.username]))
