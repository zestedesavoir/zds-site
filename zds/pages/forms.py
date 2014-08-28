# coding: utf-8
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder
from crispy_forms.bootstrap import StrictButton

from django import forms


class AssocSubscribeForm(forms.Form):
    full_name = forms.CharField(
        label=u'Qui êtes vous ?',
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': u'M/Mme Prénom Nom'
            }
        )
    )

    email = forms.EmailField(
        label=u'Adresse courriel',
        required=True,
    )

    adresse = forms.CharField(
        label=u'Adresse',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': u'Votre adresse complète (rue, code postal, ville, pays...)'
            }
        )
    )

    justification = forms.CharField(
        label=u'Pourquoi voulez-vous adhérer à l\'association ?',
        required=False,
        max_length=3000,
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
            Field('full_name'),
            Field('email'),
            Field('adresse'),
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