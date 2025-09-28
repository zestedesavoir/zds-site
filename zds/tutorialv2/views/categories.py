from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.models import SubCategory


class EditCategoriesForm(forms.Form):
    subcategory = forms.ModelMultipleChoiceField(
        label=_("Sélectionnez les catégories qui correspondent à la publication."),
        queryset=SubCategory.objects.order_by("title").all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    error_messages = {
        "no_category_but_public": _("Vous devez choisir au moins une catégorie, car ce contenu est déjà publié.")
    }

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.content = content

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("subcategory", template="crispy/checkboxselectmultiple.html"),
            StrictButton(_("Valider"), type="submit"),
        )

    def clean_subcategory(self):
        subcategory = self.cleaned_data["subcategory"]
        # Forbid removing all categories of a validated content
        if self.content.in_public() and not subcategory:
            raise ValidationError(message=self.error_messages["no_category_but_public"])
        return subcategory


class EditCategoriesView(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormView):
    template_name = "tutorialv2/edit/categories.html"
    model = PublishableContent
    form_class = EditCategoriesForm

    def get_initial(self):
        initial = super().get_initial()
        initial["subcategory"] = self.object.subcategory.all()
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.object
        return kwargs

    def form_valid(self, form):
        content = self.object

        content.subcategory.clear()
        for subcat in form.cleaned_data["subcategory"]:
            content.subcategory.add(subcat)

        self.success_url = reverse("content:view", args=[content.pk, content.slug])

        return super().form_valid(form)
