# coding: utf-8

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Hidden
from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from zds.mp.models import PrivateTopic
from zds.utils.forms import CommonLayoutEditor


class PrivateTopicForm(forms.Form):
    participants = forms.CharField(
        label='Participants',
        widget=forms.TextInput(
            attrs={
                'placeholder': u'Les participants doivent '
                u'être séparés par une virgule.',
                'required': 'required',
                'data-autocomplete': '{ "type": "multiple" }'}))

    title = forms.CharField(
        label='Titre',
        max_length=PrivateTopic._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required'
            }
        )
    )

    subtitle = forms.CharField(
        label='Sous-titre',
        max_length=PrivateTopic._meta.get_field('subtitle').max_length,
        required=False
    )

    text = forms.CharField(
        label='Texte',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.',
                'required': 'required'
            }
        )
    )

    def __init__(self, username, *args, **kwargs):
        super(PrivateTopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.username = username

        self.helper.layout = Layout(
            Field('participants', autocomplete='off'),
            Field('title', autocomplete='off'),
            Field('subtitle', autocomplete='off'),
            CommonLayoutEditor(),
        )

    def clean(self):
        cleaned_data = super(PrivateTopicForm, self).clean()

        participants = cleaned_data.get('participants')
        title = cleaned_data.get('title')
        text = cleaned_data.get('text')

        if participants is not None and participants.strip() == '':
            self._errors['participants'] = self.error_class(
                [u'Le champ participants ne peut être vide'])

        if participants is not None and participants.strip() != '':
            receivers = participants.strip().split(',')
            for receiver in receivers:
                if User.objects.filter(username__exact=receiver.strip()).count() == 0 and receiver.strip() != '':
                    self._errors['participants'] = self.error_class(
                        [u'Un des participants saisi est introuvable'])
                elif receiver.strip().lower() == self.username.lower():
                    self._errors['participants'] = self.error_class(
                        [u'Vous ne pouvez pas vous écrire à vous-même !'])

        if title is not None and title.strip() == '':
            self._errors['title'] = self.error_class(
                [u'Le champ titre ne peut être vide'])

        if text is not None and text.strip() == '':
            self._errors['text'] = self.error_class(
                [u'Le champ text ne peut être vide'])

        return cleaned_data


class PrivatePostForm(forms.Form):
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
        super(PrivatePostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'zds.mp.views.answer') + '?sujet=' + str(topic.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_post', '{{ last_post_pk }}'),
        )

        if topic.alone():
            self.helper['text'].wrap(
                Field,
                placeholder=u'Vous êtes seul dans cette conversation, '
                u'vous ne pouvez plus y écrire.',
                disabled=True)

    def clean(self):
        cleaned_data = super(PrivatePostForm, self).clean()

        text = cleaned_data.get('text')

        if text is not None and text.strip() == '':
            self._errors['text'] = self.error_class(
                [u'Le champ text ne peut être vide'])

        return cleaned_data
