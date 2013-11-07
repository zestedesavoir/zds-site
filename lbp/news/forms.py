# -*- coding: utf-8 -*-

from django import forms
from django.conf import settings
from django.forms.models import ModelForm

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
        max_length=200,
        required=False
    )

    text = forms.CharField(
        label='Texte',
        required=False,
        widget=forms.Textarea,
    )

    image = forms.ImageField(
        label='Image de la news (max. '+str(settings.IMAGE_MAX_SIZE/1024)+' Ko)'
    , required=False)
    
    tags = forms.CharField(
        label='Tags',
        max_length=80,
        required=False
    )
    
    category = forms.ModelMultipleChoiceField(
        label = "Catégorie",
        queryset=Category.objects.all(),
        required = False,
    )    
    

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('text'),
            Field('tags'),
            Field('category'),
            Field('image'),
            
            Submit('submit', 'Valider'),
        )
        super(NewsForm, self).__init__(*args, **kwargs)
        
class CommentForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)