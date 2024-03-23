from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

from django import forms
from django.contrib import messages
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("subcategory", template="crispy/checkboxselectmultiple.html"),
            StrictButton(_("Valider"), type="submit"),
        )


class EditCategoriesView(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormView):
    template_name = "tutorialv2/edit/categories.html"
    model = PublishableContent
    form_class = EditCategoriesForm

    def get_initial(self):
        initial = super().get_initial()
        initial["subcategory"] = self.object.subcategory.all()
        return initial

    def form_valid(self, form):
        publishable = self.object

        # Forbid removing all categories of a validated content
        if publishable.in_public() and not form.cleaned_data["subcategory"]:
            messages.error(
                self.request, _("Vous devez choisir au moins une catégorie, car ce contenu est déjà publié.")
            )
            return self.form_invalid(form)

        # Update categories
        publishable.subcategory.clear()
        for subcat in form.cleaned_data["subcategory"]:
            publishable.subcategory.add(subcat)

        self.success_url = reverse("content:view", args=[publishable.pk, publishable.slug])

        return super().form_valid(form)
