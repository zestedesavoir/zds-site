# coding: utf-8

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Submit, Field


class ArticleForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80
    )

    description = forms.CharField(
        max_length=200
    )

    text = forms.CharField(
        label='Texte',
        required=False,
        widget=forms.Textarea
    )
    
    image = forms.ImageField(
        label='Selectionnez une image', 
        required=False)

    tags = forms.CharField(
        label='Tags',
        max_length=80,
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('text'),
            Field('image'),
            Field('tags'),
            Submit('submit', 'Valider'),
        )
        super(ArticleForm, self).__init__(*args, **kwargs)
