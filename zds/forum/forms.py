# coding: utf-8

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

from zds.utils.forms import CommonLayoutEditor


class TopicForm(forms.Form):
    title = forms.CharField(
    	label = 'Titre',
    	max_length = 80
    )

    subtitle = forms.CharField(
    	label = 'Sous-titre',
    	max_length=255, 
    	required=False,
    )

    text = forms.CharField(
    	label = 'Texte',
    	widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(TopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title', autocomplete='off'),
            Field('subtitle', autocomplete='off'),
            CommonLayoutEditor(),
        )


class PostForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class AlertForm(forms.Form):
    text = forms.CharField()