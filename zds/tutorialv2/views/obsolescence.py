from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Layout
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import BooleanField, CharField, HiddenInput, Textarea
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils import get_current_user


class EditObsolescenceForm(forms.Form):
    is_obsolete = BooleanField(label=_("La publication est obsolète"), required=False)
    text = CharField(
        label="Description de l'obsolescence",
        max_length=PublishableContent._meta.get_field("obsolescence_description").max_length,
        required=False,
        widget=Textarea(attrs={"placeholder": _("Votre message au format Markdown.")}),
    )

    def __init__(self, content, *args, **kwargs):
        next_url = kwargs.pop("next_url", None)
        kwargs["initial"] = {"is_obsolete": content.is_obsolete, "text": content.obsolescence_description}
        super().__init__(*args, **kwargs)

        self.fields["next_url"] = CharField(
            widget=HiddenInput(),
            required=False,
            initial=next_url or "",
        )

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse("content:edit-obsolescence", kwargs={"pk": content.pk})
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "edit-obsolescence"

        self.helper.layout = Layout(
            Field("is_obsolete"),
            Field("text"),
            Field("next_url"),
            ButtonHolder(
                StrictButton(_("Valider"), type="submit"),
            ),
        )

        self.previous_page_url = reverse("content:view", kwargs={"pk": content.pk, "slug": content.slug})


class EditObsolescenceView(LoginRequiredMixin, PermissionRequiredMixin, SingleContentFormViewMixin):
    permission_required = "tutorialv2.change_publishablecontent"
    model = PublishableContent
    form_class = EditObsolescenceForm
    success_message = _("L'obsolescence a bien été modifiée.")
    next_url = CharField(widget=HiddenInput(), required=False)
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
        self.object.is_obsolete = form.cleaned_data["is_obsolete"]
        self.object.obsolescence_description = form.cleaned_data["text"]
        self.object.save()
        messages.success(self.request, self.success_message)
        signals.obsolescence_management.send(sender=self.__class__, performer=get_current_user(), content=self.object)
        next_url = form.cleaned_data.get("next_url")
        if next_url:
            self.success_url = next_url
        return super().form_valid(form)
