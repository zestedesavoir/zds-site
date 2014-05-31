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
    
    adresse1 = forms.CharField(
        label=u'Adresse',
        required=True,
    )
    
    adresse2 = forms.CharField(
        label=u'Adresse (suite)',
        required=False,
    )
    
    code_postal = forms.CharField(
        label='Code Postal',
        required=True,
    )
    
    ville = forms.CharField(
        label='Ville',
        required=True,
    )
    
    pays = forms.CharField(
        label='Pays',
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
            Field('adresse1'),
            Field('adresse2'),
            Field('code_postal'),
            Field('ville'),
            Field('pays'),
            Field('justification'),
            ButtonHolder(
                Submit('submit', 'Valider', css_class='button'),
            )
        )
