# coding: utf-8

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, HTML


class NewsletterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                HTML(u'<input type="email" name="email" placeholder="E-mail" '
                u'required="required" pattern="[^@]+@[^@]+\.[a-zA-Z]{2,6}">'),
                HTML('<button type="submit" title="Inscription newsletter"><span>OK</span></button>'),
            ))
        super(NewsletterForm, self).__init__(*args, **kwargs)
