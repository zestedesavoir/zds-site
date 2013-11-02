# coding: utf-8

from django import forms
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Submit, Field


class ProjectForm(forms.Form):
    
    title = forms.CharField(
        label='Titre',
        max_length=80
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea
    )
    
    image = forms.ImageField(
        label='Selectionnez l\'image du projet',
        help_text='max. '+str(settings.IMAGE_MAX_SIZE/1024)+' Ko'
    , required=False)
    

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('image'),
            Submit('submit', 'Valider'),
        )
        super(ProjetForm, self).__init__(*args, **kwargs)
