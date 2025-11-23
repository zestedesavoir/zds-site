from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Layout
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2 import signals as signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils import get_current_user
from zds.utils.forms import TagValidator


class EditTagsForm(forms.Form):
    tags = forms.CharField(
        label=_("Tags séparés par des virgules (exemple : python,api,web) :"),
        max_length=64,
        required=False,
        widget=forms.TextInput(),
        error_messages={"max_length": _("La liste de tags saisie dépasse la longueur maximale autorisée.")},
    )

    def __init__(self, content, db_content, *args, **kwargs):
        self.db_content = db_content
        kwargs["initial"] = {"tags": ", ".join(db_content.tags.values_list("title", flat=True))}
        super().__init__(*args, **kwargs)

        self.fields["tags"].widget.attrs.update(
            {
                "data-autocomplete": '{ "type": "multiple", "fieldname": "title", "url": "'
                + reverse("api:utils:tags-list")
                + '?search=%s" }',
            }
        )

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_id = "edit-tags"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_action = reverse("content:edit-tags", kwargs={"pk": content.pk})
        self.helper.layout = Layout(
            HTML(
                """<p>Les tags permettent de grouper les publications plus finement que les catégories.
                    Par exemple, vous pouvez indiquer une technologie ou une sous-discipline.
                     Consultez <a href="{}">la page des tags</a> pour voir des exemples.""".format(
                    reverse("content:tags")
                )
            ),
            Field("tags"),
            StrictButton("Valider", type="submit"),
        )
        self.previous_page_url = reverse("content:view", kwargs={"pk": content.pk, "slug": content.slug})

    def clean_tags(self):
        validator = TagValidator()
        cleaned_tags = self.cleaned_data.get("tags")
        if not validator.validate_raw_string(cleaned_tags):
            self.add_error("tags", self.error_class(validator.errors))
        return cleaned_tags


class EditTags(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditTagsForm
    success_message = _("Les tags ont bien été modifiés.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        kwargs["db_content"] = self.object
        return kwargs

    def form_valid(self, form):
        self.object.tags.clear()
        self.object.add_tags(form.cleaned_data["tags"].split(","))
        self.object.save()
        messages.success(self.request, EditTags.success_message)
        signals.tags_management.send(sender=self.__class__, performer=get_current_user(), content=self.object)
        return redirect(form.previous_page_url)
