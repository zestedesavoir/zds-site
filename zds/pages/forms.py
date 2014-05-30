# coding: utf-8
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Field, ButtonHolder, Submit

from django import forms


class AssocSubscribeForm(forms.Form):
    first_name = forms.CharField(
        label=u'Prénom',
        required=True,
    )

    surname = forms.CharField(
        label='Nom de famille',
        required=True,
    )

    email = forms.EmailField(
        label='Adresse e-mail',
        required=True,
    )

    justification = forms.CharField(
        label='Raison de la demande',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': u'Décrivez ici la raison de votre demande d\'adhésion à l\'association.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(AssocSubscribeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('first_name'),
            Field('surname'),
            Field('email'),
            Field('justification'),
            ButtonHolder(
                Submit('submit', 'Valider', css_class='button'),
            )
        )
