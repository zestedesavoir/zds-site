# coding: utf-8

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Submit, Field
from zds.utils.models import SubCategory


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

    subcategory = forms.ModelMultipleChoiceField(
        label = "Sous-catégories de votre article",
        queryset = SubCategory.objects.all(),
        required = True,
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('text'),
            Field('image'),
            Field('subcategory'),
            Submit('submit', 'Valider'),
        )
        super(ArticleForm, self).__init__(*args, **kwargs)

class ReactionForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class AlertForm(forms.Form):
    text = forms.CharField()