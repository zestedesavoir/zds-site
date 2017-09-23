# coding: utf-8
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder
from crispy_forms.bootstrap import StrictButton

from django import forms
from django.utils.translation import ugettext_lazy as _


class AssocSubscribeForm(forms.Form):
    full_name = forms.CharField(
        label=_(u'Qui êtes-vous&nbsp;?'),
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'M/Mme Prénom Nom')
            }
        )
    )

    email = forms.EmailField(
        label=_(u'Adresse courriel'),
        required=True,
    )

    birthdate = forms.CharField(
        label=_(u'Date de naissance'),
        required=True,
    )

    address = forms.CharField(
        label=_(u'Adresse'),
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre adresse complète (rue, code postal, ville, pays...)')
            }
        )
    )

    justification = forms.CharField(
        label=_(u'Pourquoi voulez-vous adhérer à l\'association&nbsp;?'),
        required=False,
        max_length=3000,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Décrivez ici la raison de votre demande d\'adhésion à l\'association (3000 caractère'
                                 u's maximum).')
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
            Field('birthdate'),
            Field('address'),
            Field('justification'),
            ButtonHolder(
                StrictButton(_('Valider'), type='submit'),
            )
        )
