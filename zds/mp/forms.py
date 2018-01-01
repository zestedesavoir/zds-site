from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Hidden, ButtonHolder, HTML
from crispy_forms.bootstrap import StrictButton

from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from zds.mp.models import PrivateTopic
from zds.mp.validators import ParticipantsStringValidator, TitleValidator, TextValidator
from zds.utils.forms import CommonLayoutEditor


class PrivateTopicForm(forms.Form, ParticipantsStringValidator, TitleValidator, TextValidator):
    participants = forms.CharField(
        label=_('Participants'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Les participants doivent '
                                 'être séparés par une virgule.'),
                'required': 'required',
                'data-autocomplete': '{ "type": "multiple", "url": "/api/membres/?search=%s" }'}))

    title = forms.CharField(
        label=_('Titre'),
        max_length=PrivateTopic._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required'
            }
        )
    )

    subtitle = forms.CharField(
        label=_('Sous-titre'),
        max_length=PrivateTopic._meta.get_field('subtitle').max_length,
        required=False
    )

    text = forms.CharField(
        label='Texte',
        widget=forms.Textarea(
            attrs={
                'placeholder': _('Votre message au format Markdown.'),
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
            HTML("{% include 'misc/hat_choice.html' %}"),
        )

    def clean(self):
        cleaned_data = super(PrivateTopicForm, self).clean()

        self.validate_participants(cleaned_data.get('participants'), self.username)
        self.validate_title(cleaned_data.get('title'))
        self.validate_text(cleaned_data.get('text'))

        return cleaned_data

    def throw_error(self, key=None, message=None):
        self._errors[key] = self.error_class([message])


class PrivateTopicEditForm(forms.ModelForm, TitleValidator):

    class Meta:
        model = PrivateTopic
        fields = ['title', 'subtitle']

    def __init__(self, *args, **kwargs):
        super(PrivateTopicEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('subtitle'),
            ButtonHolder(
                StrictButton(_('Mettre à jour'), type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(PrivateTopicEditForm, self).clean()
        self.validate_title(cleaned_data.get('title'))
        return cleaned_data

    def throw_error(self, key=None, message=None):
        self._errors[key] = self.error_class([message])


class PrivatePostForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': _('Votre message au format Markdown.'),
                'required': 'required'
            }
        )
    )

    def __init__(self, topic, *args, **kwargs):
        super(PrivatePostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('private-posts-new', args=[topic.pk, topic.slug()])
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            HTML("{% include 'misc/hat_choice.html' with edited_message=post %}"),
            Hidden('last_post', '{{ last_post_pk }}'),
        )

        if topic.alone():
            self.helper['text'].wrap(
                Field,
                placeholder=_('Vous êtes seul dans cette conversation, '
                              'vous ne pouvez plus y écrire.'),
                disabled=True)

    def clean(self):
        cleaned_data = super(PrivatePostForm, self).clean()

        text = cleaned_data.get('text')

        if text is not None and not text.strip():
            self._errors['text'] = self.error_class(
                [_('Le champ text ne peut être vide')])

        return cleaned_data
