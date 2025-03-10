import logging
from datetime import datetime

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, ButtonHolder, Field, Layout
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms import CharField, Textarea, TextInput, forms
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, FormView

from zds.gallery.models import Gallery
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.utils import get_bot_account
from zds.mp.utils import send_message_mp, send_mp
from zds.tutorialv2.forms import ContentForm, FormWithTitle
from zds.tutorialv2.mixins import FormWithPreview, SingleContentFormViewMixin, SingleContentViewMixin
from zds.tutorialv2.models import CONTENT_TYPE_LIST
from zds.tutorialv2.models.database import PublishableContent, Validation
from zds.tutorialv2.utils import init_new_repo
from zds.tutorialv2.views.authors import RemoveAuthorFromContent
from zds.utils.forms import IncludeEasyMDE
from zds.utils.models import get_hat_from_settings
from zds.utils.uuslug_wrapper import slugify

logger = logging.getLogger(__name__)


class CreateContentView(LoggedWithReadWriteHability, FormView):
    template_name = "tutorialv2/create/content.html"
    model = PublishableContent
    form_class = ContentForm

    def get_form(self, form_class=ContentForm):
        form = super().get_form(form_class)
        content_type = self.kwargs["created_content_type"]
        form.initial["type"] = content_type if content_type in CONTENT_TYPE_LIST else "TUTORIAL"
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editorial_line_link"] = settings.ZDS_APP["content"]["editorial_line_link"]
        context["site_name"] = settings.ZDS_APP["site"]["literal_name"]
        return context

    def form_valid(self, form):
        self.content = PublishableContent(
            title=form.cleaned_data["title"],
            type=form.cleaned_data["type"],
            licence=self.request.user.profile.licence,  # Use the preferred license of the user if it exists
            creation_date=datetime.now(),
        )

        self.content.gallery = Gallery.objects.create(
            title=self.content.title,
            slug=slugify(self.content.title),
            pubdate=datetime.now(),
        )

        self.content.save()  # Commit to database before updating relationships

        # Update relationships
        self.content.authors.add(self.request.user)
        self.content.ensure_author_gallery()

        # Create a new git repository
        init_new_repo(self.content)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("content:view", args=[self.content.pk, self.content.slug])


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


class EditIntroductionForm(forms.Form):
    introduction = CharField(
        label=_("Introduction"),
        required=False,
        widget=Textarea(
            attrs={"placeholder": _("Votre introduction, au format Markdown."), "class": "md-editor preview-source"}
        ),
    )

    commit_message = CharField(
        label=_("Message de suivi"),
        max_length=400,
        required=False,
        widget=TextInput(attrs={"placeholder": _("Un résumé de vos ajouts et modifications.")}),
    )

    def __init__(self, versioned_content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("content:edit-introduction", kwargs={"pk": versioned_content.pk})
        self.helper.layout = Layout(
            IncludeEasyMDE(),
            Field("introduction"),
            ButtonHolder(
                StrictButton(_("Aperçu"), type="preview", name="preview", css_class="btn btn-grey preview-btn"),
            ),
            HTML(
                """{% if form.introduction.value %}{% include "misc/preview.part.html" with text=form.introduction.value %}{% endif %}"""
            ),
            Field("commit_message"),
            ButtonHolder(StrictButton(_("Modifier"), type="submit")),
        )


class EditIntroductionView(LoginRequiredMixin, SingleContentFormViewMixin, FormWithPreview):
    model = PublishableContent
    form_class = EditIntroductionForm
    template_name = "tutorialv2/edit/introduction.html"
    success_message = _("L'introduction de la publication a bien été changée.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "preview" not in self.request.POST:
            context["gallery"] = self.object.gallery
        return context

    def get_initial(self):
        initial = super().get_initial()
        introduction = self.versioned_object.get_introduction()
        initial["introduction"] = introduction
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["versioned_content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object
        versioned = self.versioned_object

        commit_message = "Modification de l'introduction"
        if form.cleaned_data["commit_message"] != "":
            commit_message = form.cleaned_data["commit_message"]

        sha = self.update_introduction_in_repository(
            publishable, versioned, form.cleaned_data["introduction"], commit_message
        )
        self.update_sha_draft(publishable, sha)

        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("content:view", args=[self.object.pk, self.object.slug])

    @staticmethod
    def update_introduction_in_repository(publishable_content, versioned_content, introduction, commit_message):
        sha = versioned_content.repo_update_top_container(
            publishable_content.title,
            publishable_content.slug,
            introduction,
            versioned_content.get_conclusion(),
            commit_message,
        )
        return sha

    @staticmethod
    def update_sha_draft(publishable_content, sha):
        publishable_content.sha_draft = sha
        publishable_content.save()


class EditConclusionForm(forms.Form):
    conclusion = CharField(
        label=_("Conclusion"),
        required=False,
        widget=Textarea(
            attrs={"placeholder": _("Votre conclusion, au format Markdown."), "class": "md-editor preview-source"}
        ),
    )

    commit_message = CharField(
        label=_("Message de suivi"),
        max_length=400,
        required=False,
        widget=TextInput(attrs={"placeholder": _("Un résumé de vos ajouts et modifications.")}),
    )

    def __init__(self, versioned_content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("content:edit-conclusion", kwargs={"pk": versioned_content.pk})
        self.helper.layout = Layout(
            IncludeEasyMDE(),
            Field("conclusion"),
            ButtonHolder(
                StrictButton(_("Aperçu"), type="preview", name="preview", css_class="btn btn-grey preview-btn")
            ),
            HTML(
                """{% if form.conclusion.value %}{% include "misc/preview.part.html" with text=form.conclusion.value %}{% endif %}"""
            ),
            Field("commit_message"),
            ButtonHolder(StrictButton(_("Modifier"), type="submit")),
        )


class EditConclusionView(LoginRequiredMixin, SingleContentFormViewMixin, FormWithPreview):
    model = PublishableContent
    form_class = EditConclusionForm
    template_name = "tutorialv2/edit/conclusion.html"
    success_message = _("La conclusion de la publication a bien été changée.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "preview" not in self.request.POST:
            context["gallery"] = self.object.gallery
        return context

    def get_initial(self):
        initial = super().get_initial()
        conclusion = self.versioned_object.get_conclusion()
        initial["conclusion"] = conclusion
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["versioned_content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object
        versioned = self.versioned_object

        commit_message = "Modification de la conclusion"
        if form.cleaned_data["commit_message"] != "":
            commit_message = form.cleaned_data["commit_message"]

        sha = self.update_conclusion_in_repository(
            publishable, versioned, form.cleaned_data["conclusion"], commit_message
        )
        self.update_sha_draft(publishable, sha)

        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("content:view", args=[self.object.pk, self.object.slug])

    @staticmethod
    def update_conclusion_in_repository(publishable_content, versioned_content, conclusion, commit_message):
        sha = versioned_content.repo_update_top_container(
            publishable_content.title,
            publishable_content.slug,
            versioned_content.get_introduction(),
            conclusion,
            commit_message,
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
