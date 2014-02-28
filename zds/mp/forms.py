# coding: utf-8

from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Hidden

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
    text = forms.CharField(
        label = '',
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, topic, user, *args, **kwargs):
        super(PrivatePostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.mp.views.answer') + '?sujet=' + str(topic.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_post', '{{ last_post_pk }}'),
        )

        if topic.antispam(user):
            self.helper['text'].wrap(
                Field, 
                placeholder = u'Vous ne pouvez pas encore poster sur ce MP (protection antispam de 15 min).',
                disabled = True
            )
