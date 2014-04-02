# coding: utf-8

from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Hidden
from crispy_forms_foundation.layout import ButtonHolder
from crispy_forms.bootstrap import StrictButton

from zds.utils.forms import CommonLayoutEditor
from zds.forum.models import Forum


class TopicForm(forms.Form):
    title = forms.CharField(
    	label = 'Titre',
    	max_length = 80,
        widget = forms.TextInput(
            attrs = {
                'required': 'required',
            }
        )
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
                'placeholder': 'Votre message au format Markdown.',
                'required':'required'
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
        
    def clean(self):
        cleaned_data = super(TopicForm, self).clean()

        title = cleaned_data.get('title')
        text = cleaned_data.get('text')
        
        if title is not None and title.strip() == '':
            self._errors['title'] = self.error_class([u'Le champ titre ne peut être vide'])
            if 'title' in cleaned_data:
                del cleaned_data['title']
        
        if text is not None and text.strip() == '':
            self._errors['text'] = self.error_class([u'Le champ text ne peut être vide'])
            if 'text' in cleaned_data:
                del cleaned_data['text']
        
        return cleaned_data

class PostForm(forms.Form):
    text = forms.CharField(
        label = '',
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.',
                'required':'required'
            }
        )
    )

    def __init__(self, topic, user, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_post', '{{ last_post_pk }}'),
        )

        if topic.antispam(user):
            self.helper['text'].wrap(
                Field, 
                placeholder = u'Vous ne pouvez pas encore poster sur ce topic (protection antispam de 15 min).',
                disabled = True
            )
        elif topic.is_locked:
            self.helper['text'].wrap(
                Field, 
                placeholder = u'Ce topic est verrouillé.',
                disabled = True
            )
    
    def clean(self):
        cleaned_data = super(PostForm, self).clean()

        text = cleaned_data.get('text')

        if text.strip() == '':
            self._errors['text'] = self.error_class([u'Le champ text ne peut être vide'])
            if 'text' in cleaned_data:
                del cleaned_data['text']
        
        return cleaned_data

class MoveTopicForm(forms.Form):
    
    forum = forms.ModelChoiceField(
        label = "Forum",
        queryset = Forum.objects.all(),
        required = True,
    )

    def __init__(self, topic, *args, **kwargs):
        super(MoveTopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.forum.views.move_topic') + '?sujet=' + str(topic.pk)
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('forum'),
            ButtonHolder(
                StrictButton('Valider', type = 'submit', css_class = 'btn-submit'),
            )
        )
