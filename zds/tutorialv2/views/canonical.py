from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Layout
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils import get_current_user


class EditCanonicalLinkForm(forms.Form):
    source = forms.URLField(
        label=_(
            """Si votre contenu est publié en dehors de Zeste de Savoir (blog, site personnel, etc.),
                       indiquez le lien de la publication originale :"""
        ),
        max_length=PublishableContent._meta.get_field("source").max_length,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("https://...")}),
        error_messages={"invalid": _("Entrez un lien valide.")},
    )

    def __init__(self, content, *args, **kwargs):
        kwargs["initial"] = {"source": content.source}
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse("content:edit-canonical-link", kwargs={"pk": content.pk})
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "edit-canonical-link"

        self.helper.layout = Layout(
            Field("source"),
            ButtonHolder(
                StrictButton(_("Valider"), type="submit"),
            ),
        )

        self.previous_page_url = reverse("content:view", kwargs={"pk": content.pk, "slug": content.slug})


class EditCanonicalLinkView(LoginRequiredMixin, SingleContentFormViewMixin):
    model = PublishableContent
    form_class = EditCanonicalLinkForm
    success_message = _("Le lien canonique a bien été modifié.")
    modal_form = True
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        content = get_object_or_404(PublishableContent, pk=self.kwargs["pk"])
        success_url_kwargs = {"pk": content.pk, "slug": content.slug}
        self.success_url = reverse("content:view", kwargs=success_url_kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.object
        return kwargs

    def form_invalid(self, form):
        form.previous_page_url = self.success_url
        return super().form_invalid(form)

    def form_valid(self, form):
        self.object.source = form.cleaned_data["source"]
        self.object.save()
        messages.success(self.request, self.success_message)
        signals.canonical_link_management.send(sender=self.__class__, performer=get_current_user(), content=self.object)
        return super().form_valid(form)
