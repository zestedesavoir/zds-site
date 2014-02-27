# coding: utf-8

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

from zds.utils.forms import CommonLayoutEditor


class PrivateTopicForm(forms.Form):
    participants = forms.CharField(
    	label = 'Participants',
    	widget = forms.TextInput(
            attrs = {
                'placeholder': u'Les participants doivent être séparés par une virgule.'
            }
        )
    )

    title = forms.CharField(
    	label = 'Titre',
    	max_length=80
    )

    subtitle = forms.CharField(
    	label = 'Sous-titre',
    	max_length=255, 
    	required=False
    )

    text = forms.CharField(
        label = 'Texte',
        required = False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(PrivateTopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
        	Field('participants', autocomplete='off'),
            Field('title', autocomplete='off'),
            Field('subtitle', autocomplete='off'),
            CommonLayoutEditor(),
        )


class PrivatePostForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)
