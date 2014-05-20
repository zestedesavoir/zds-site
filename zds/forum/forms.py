# coding: utf-8

import re

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Field, Hidden
from zds.forum.models import Forum, Topic, sub_tag
from zds.utils.forms import CommonLayoutEditor


class TopicForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=Topic._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    subtitle = forms.CharField(
        label='Sous-titre',
        max_length=Topic._meta.get_field('subtitle').max_length,
        required=False,
    )

    text = forms.CharField(
        label='Texte',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.',
                'required': 'required'
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

        if title is not None:
            if title.strip() == '':
                self._errors['title'] = self.error_class(
                    [u'Le champ titre ne peut être vide'])
                if 'title' in cleaned_data:
                    del cleaned_data['title']
            elif re.sub(ur"(?P<start>)(\[.*?\])(?P<end>)", sub_tag, title) \
                    .strip() == '':
                self._errors['title'] = self.error_class(
                    [u'Le titre ne peux pas contenir uniquement des tags'])
        if text is not None and text.strip() == '':
            self._errors['text'] = self.error_class(
                [u'Le champ text ne peut être vide'])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        if text is not None and len(text) > settings.MAX_POST_LENGTH:
            self._errors['text'] = self.error_class(
                [(u'Ce message est trop long, il ne doit pas dépasser {0} '
                  u'caractères').format(settings.MAX_POST_LENGTH)])

        return cleaned_data


class PostForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.',
                'required': 'required'
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
            if 'text' not in self.initial:
                self.helper['text'].wrap(
                    Field,
                    placeholder=u'Vous ne pouvez pas encore poster u\
                    usur ce topic (protection antispam de 15 min).',
                    disabled=True)
        elif topic.is_locked:
            self.helper['text'].wrap(
                Field,
                placeholder=u'Ce topic est verrouillé.',
                disabled=True
            )

    def clean(self):
        cleaned_data = super(PostForm, self).clean()

        text = cleaned_data.get('text')

        if text.strip() == '':
            self._errors['text'] = self.error_class(
                [u'Le champ text ne peut être vide'])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        if len(text) > settings.MAX_POST_LENGTH:
            self._errors['text'] = self.error_class(
                [(u'Ce message est trop long, il ne doit pas dépasser {0} '
                  u'caractères').format(settings.MAX_POST_LENGTH)])

        return cleaned_data


class MoveTopicForm(forms.Form):

    forum = forms.ModelChoiceField(
        label="Forum",
        queryset=Forum.objects.all(),
        required=True,
    )

    def __init__(self, topic, *args, **kwargs):
        super(MoveTopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'zds.forum.views.move_topic') + '?sujet=' + str(topic.pk)
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('forum'),
            StrictButton('Valider', type='submit', css_class='button tiny'),
        )
