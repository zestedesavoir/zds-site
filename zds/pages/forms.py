# coding: utf-8
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder
from crispy_forms.bootstrap import StrictButton

from django import forms


class AssocSubscribeForm(forms.Form):
    first_name = forms.CharField(
        label=u'Prénom',
        max_length= 30,
        required=True,
    )

    surname = forms.CharField(
        label='Nom de famille',
        max_length= 30,
        required=True,
    )

    email = forms.EmailField(
        label='Adresse courriel',
        required=True,
    )

    adresse = forms.CharField(
        label=u'Adresse',
        max_length= 38,
        required=True,
    )

    adresse_complement = forms.CharField(
        label=u'Complément d\'adresse',
        max_length= 38,
        required=False,
    )

    code_postal = forms.CharField(
        label='Code Postal',
        max_length= 5,
        required=True,
    )

    ville = forms.CharField(
        label='Ville',
        max_length= 38,
        required=True,
    )

    pays = forms.CharField(
        label='Pays',
        max_length= 38,
        required=True,
    )

    justification = forms.CharField(
        label='Pourquoi voulez-vous adhérer à l\'association ?',
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
            Field('adresse'),
            Field('adresse_complement'),
            Field('code_postal'),
            Field('ville'),
            Field('pays'),
            Field('justification'),
            ButtonHolder(
                StrictButton('Valider', type='submit'),
            )
        )

    def clean(self):
        cleaned_data = super(AssocSubscribeForm, self).clean()
        justification = cleaned_data.get('justification')
        
        if justification is not None and len(justification) > 3000:
            self._errors['justification'] = self.error_class(
                [(u'Ce message est trop long, il ne doit pas dépasser 3000 caractères')])