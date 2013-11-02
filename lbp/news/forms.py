# -*- coding: utf-8 -*-

from django import forms
from django.conf import settings
from django.forms.models import ModelForm
from ajax_select import make_ajax_field

from models import News
from lbp.project.models import Category
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Submit, Field


class NewsForm(forms.Form):
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
        label='Selectionnez l\'image de la news',
        help_text='max. '+str(settings.IMAGE_MAX_SIZE/1024)+' Ko'
    , required=False)
    
    tags = forms.CharField(
        label='Tags',
        max_length=80,
        required=False
    )
    
    category = make_ajax_field(News, 'category', 'category', show_help_text="saisir les catégories")
    

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('text'),
            Field('tags'),
            Field('image'),
            Field('category'),
            Submit('submit', 'Valider'),
        )
        super(NewsForm, self).__init__(*args, **kwargs)
