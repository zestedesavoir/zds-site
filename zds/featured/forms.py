from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Layout
from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.featured.models import FeaturedMessage, FeaturedResource


class FeaturedResourceForm(forms.ModelForm):
    class Meta:
        model = FeaturedResource

        fields = ["title", "type", "authors", "image_url", "url"]

        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("Titre de la Une")}),
            "type": forms.TextInput(attrs={"placeholder": _("ex: Un projet, Un article, Un tutoriel...")}),
            "authors": forms.TextInput(attrs={"placeholder": _("Des auteurs (ou pas) ?")}),
            "image_url": forms.URLInput(
                attrs={"placeholder": _("Lien vers l'image de la Une (dimensions: 228x228px).")}
            ),
            "url": forms.URLInput(attrs={"placeholder": _("Lien vers la ressource.")}),
        }

    major_update = forms.BooleanField(
        label=_("Mise à jour majeure (fera passer la Une en première position lors d'un changement)"),
        initial=False,
        required=False,
    )

    pubdate = forms.DateTimeField(
        label=_("Date de publication (exemple: 25/12/2015 15:00)"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    request = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        hide_major_update_field = kwargs.pop("hide_major_update_field", False)

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("featured:resource-create")

        fields = [Field("request"), Field("title"), Field("type"), Field("authors"), Field("image_url"), Field("url")]

        if not hide_major_update_field:
            fields.append(Field("major_update"))

        fields.extend(
            [
                Field("pubdate"),
                ButtonHolder(
                    StrictButton(_("Enregistrer"), type="submit"),
                ),
            ]
        )

        self.helper.layout = Layout(*fields)


class FeaturedMessageForm(forms.ModelForm):
    class Meta:
        model = FeaturedMessage

        fields = ["hook", "message", "url"]

        widgets = {
            "hook": forms.TextInput(attrs={"placeholder": _('Mot d\'accroche court ("Nouveau !")')}),
            "message": forms.TextInput(attrs={"placeholder": _("Message à afficher")}),
            "url": forms.URLInput(attrs={"placeholder": _("Lien vers la description de la ressource")}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("featured:message-create")

        self.helper.layout = Layout(
            Field("hook"),
            Field("message"),
            Field("url"),
            ButtonHolder(
                StrictButton(_("Enregistrer"), type="submit"),
            ),
        )
