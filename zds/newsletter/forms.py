# coding: utf-8

from captcha.fields import CaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Div, Fieldset, Submit, Field, \
    HTML
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class NewsletterForm(forms.Form):
    email = forms.EmailField(label='Adresse email')

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(

                Field('email'),
                Submit('submit', 'Valider'),
        )
        super(NewsletterForm, self).__init__(*args, **kwargs)