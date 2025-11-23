from datetime import datetime

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Layout
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.models import Profile
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.models import Licence


class EditContentLicenseForm(forms.Form):
    license = forms.ModelChoiceField(
        label=_("Licence de votre publication : "),
        queryset=Licence.objects.order_by("title").all(),
        required=True,
        empty_label=_("Choisir une licence"),
        error_messages={
            "required": _("Merci de choisir une licence."),
            "invalid_choice": _("Merci de choisir une licence valide dans la liste."),
        },
    )

    update_preferred_license = forms.BooleanField(
        label=_("Je souhaite utiliser cette licence comme choix par défaut pour mes futures publications."),
        required=False,
    )

    def __init__(self, versioned_content, *args, **kwargs):
        kwargs["initial"] = {"license": versioned_content.licence}
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_id = "edit-license"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_action = reverse("content:edit-license", kwargs={"pk": versioned_content.pk})
        self.previous_page_url = reverse(
            "content:view", kwargs={"pk": versioned_content.pk, "slug": versioned_content.slug}
        )
        self._create_layout()

        if "type" in self.initial:
            self.helper["type"].wrap(Field, disabled=True)

    def _create_layout(self):
        self.helper.layout = Layout(
            HTML(
                """<p>{} encourage l'utilisation de licences facilitant le partage,
                    telles que les licences <a href="https://creativecommons.org/">Creative Commons</a>.</p>
                    <p>Pour choisir la licence de votre publication, aidez-vous de la
                    <a href="{}" alt="{}">présentation
                    des différentes licences proposées sur le site</a>.</p>""".format(
                    settings.ZDS_APP["site"]["literal_name"],
                    settings.ZDS_APP["site"]["licenses"]["licence_info_title"],
                    settings.ZDS_APP["site"]["licenses"]["licence_info_link"],
                )
            ),
            Field("license"),
            Field("update_preferred_license"),
            StrictButton("Valider", type="submit"),
        )


class EditContentLicense(LoginRequiredMixin, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditContentLicenseForm
    success_message_license = _("La licence de la publication a bien été changée.")
    success_message_profile_update = _("Votre licence préférée a bien été mise à jour.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["versioned_content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object
        new_licence = form.cleaned_data["license"]

        # Update licence in database
        publishable.licence = new_licence
        publishable.update_date = datetime.now()
        publishable.save()

        # Update licence in repository
        self.versioned_object.licence = new_licence
        sha = self.versioned_object.repo_update_top_container(
            publishable.title,
            publishable.slug,
            self.versioned_object.get_introduction(),
            self.versioned_object.get_conclusion(),
            f"Nouvelle licence ({new_licence})",
        )

        # Update relationships in database
        publishable.sha_draft = sha
        publishable.save()

        messages.success(self.request, EditContentLicense.success_message_license)

        # Update the preferred license of the user
        if form.cleaned_data["update_preferred_license"]:
            profile = get_object_or_404(Profile, user=self.request.user)
            profile.licence = new_licence
            profile.save()
            messages.success(self.request, EditContentLicense.success_message_profile_update)

        return redirect(form.previous_page_url)
