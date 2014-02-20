# coding: utf-8

from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, ButtonHolder, Submit, Field, Reset
from zds.utils.models import SubCategory


class ArticleForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80,
    )

    description = forms.CharField(
        max_length=200,
    )
    
    text = forms.CharField(
        label='Texte',
        required=False,
        widget=forms.Textarea
    )
    
    image = forms.ImageField(
        label='Selectionnez une image', 
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label = "Sous catégories de votre article",
        queryset = SubCategory.objects.all(),
        required = False
    )

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_action = reverse('zds.article.views.new')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title', autocomplete='off'),
            Field('description', autocomplete='off'),
            Field('text'),
            Field('image'),
            Field('subcategory'),
            ButtonHolder(
                Submit('submit', 'Valider'),
                Reset('reset', 'Reset'),
            ),
        )

    def clean(self):
        self._errors['subcategory'] = None
        return super(ArticleForm, self).clean()

class ReactionForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class AlertForm(forms.Form):
    text = forms.CharField()