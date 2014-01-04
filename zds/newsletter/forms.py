# coding: utf-8

from captcha.fields import CaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Div, Fieldset, Submit, Field, \
    HTML
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class NewsletterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                HTML('<input type="email" name="email" placeholder="E-mail" required="required" pattern="[^@]+@[^@]+\.[a-zA-Z]{2,6}">'),
                HTML('<button type="submit" title="Inscription newsletter"><span>OK</span></button>'),
            )
        )
        super(NewsletterForm, self).__init__(*args, **kwargs)