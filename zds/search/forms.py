import random

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class SearchForm(forms.Form):
    q = forms.CharField(
        label=_("Recherche"),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"type": "search", "required": "required", "id": "search-home"}),
    )

    model_choices = sorted(
        ((k, v[0]) for k, v in settings.ZDS_APP["search"]["search_groups"].items()), key=lambda pair: pair[1]
    )
    models = forms.MultipleChoiceField(
        label="",
        widget=forms.CheckboxSelectMultiple(attrs={"class": "search-filters", "form": "search-form"}),
        required=False,
        choices=model_choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "search-form"
        self.helper.form_class = "clearfix"
        self.helper.form_method = "get"
        self.helper.form_action = reverse("search:query")

        try:
            with (settings.BASE_DIR / "suggestions.txt").open("r") as suggestions_file:
                suggestions = ", ".join(random.sample(suggestions_file.readlines(), 5)) + "…"
        except OSError:
            suggestions = _("Mathématiques, Droit, UDK, Langues, Python…")

        self.fields["q"].widget.attrs["placeholder"] = suggestions

        self.helper.layout = Layout(
            Field("q"),
            StrictButton(_("Rechercher"), type="submit", css_class="ico-after ico-search", title=_("Rechercher")),
        )

    def clean(self):
        """Override clean() to add a field containing collections we have actually to search into."""
        cleaned_data = super().clean()

        if self.is_valid():
            if len(cleaned_data.get("models", [])) == 0:
                # Search in all collections
                cleaned_data["search_collections"] = [
                    c for _, v in settings.ZDS_APP["search"]["search_groups"].items() for c in v[1]
                ]
            else:
                # Search in collections of selected models
                cleaned_data["search_collections"] = [
                    c
                    for k, v in settings.ZDS_APP["search"]["search_groups"].items()
                    for c in v[1]
                    if k in cleaned_data["models"]
                ]

        return cleaned_data
