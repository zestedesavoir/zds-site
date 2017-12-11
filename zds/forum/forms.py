from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Hidden, HTML
from crispy_forms.bootstrap import StrictButton
from zds.forum.models import Forum, Topic
from zds.utils.forms import CommonLayoutEditor, TagValidator


class TopicForm(forms.Form):
    title = forms.CharField(
        label=_('Titre'),
        max_length=Topic._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Titre de mon sujet'),
                'required': 'required'
            }
        )
    )

    subtitle = forms.CharField(
        label=_('Sous-titre'),
        max_length=Topic._meta.get_field('subtitle').max_length,
        required=False,
    )

    tags = forms.CharField(
        label=_('Tag(s) séparés par une virgule (exemple: python,django,web)'),
        max_length=64,
        required=False,
        widget=forms.TextInput(
            attrs={
                'data-autocomplete': '{ "type": "multiple", "fieldname": "title", "url": "/api/tags/?search=%s" }'
            }
        )
    )

    text = forms.CharField(
        label='Texte',
        widget=forms.Textarea(
            attrs={
                'placeholder': _('Votre message au format Markdown.'),
                'required': 'required',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(TopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('subtitle', autocomplete='off'),
            Field('tags'),
            HTML("""<div id="topic-suggest" style="display:none;"  url="/rechercher/sujets-similaires/">
  <label>{0}</label>
  <div id="topic-result-container" data-neither="{1}"></div>
</div>"""
                 .format(_('Sujets similaires au vôtre :'), _('Aucun résultat'))),
            CommonLayoutEditor(),
        )

        if 'text' in self.initial:
            self.helper.layout.append(
                HTML("{% include 'misc/hat_choice.html' with edited_message=topic.first_post %}")
            )
        else:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' %}"))

    def clean(self):
        cleaned_data = super(TopicForm, self).clean()

        title = cleaned_data.get('title')
        text = cleaned_data.get('text')
        tags = cleaned_data.get('tags')

        if title is not None:
            if not title.strip():
                self._errors['title'] = self.error_class(
                    [_('Le champ titre ne peut être vide')])
                if 'title' in cleaned_data:
                    del cleaned_data['title']
        if text is not None and not text.strip():
            self._errors['text'] = self.error_class(
                [_('Le champ text ne peut être vide')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        if text is not None and len(text) > settings.ZDS_APP['forum']['max_post_length']:
            self._errors['text'] = self.error_class(
                [_('Ce message est trop long, il ne doit pas dépasser {0} '
                   'caractères').format(settings.ZDS_APP['forum']['max_post_length'])])

        validator = TagValidator()
        if not validator.validate_raw_string(tags):
            self._errors['tags'] = self.error_class(validator.errors)
        return cleaned_data


class PostForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': _('Votre message au format Markdown.'),
                'required': 'required',
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

        if 'text' in self.initial:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' with edited_message=post %}"))
        else:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' %}"))

        if topic.antispam(user):
            if 'text' not in self.initial:
                self.helper['text'].wrap(
                    Field,
                    placeholder=_('Vous venez de poster. Merci de patienter '
                                  'au moins 15 minutes entre deux messages consécutifs '
                                  'afin de limiter le flood.'),
                    disabled=True)
        elif topic.is_locked:
            if 'text' not in self.initial:
                self.helper['text'].wrap(
                    Field,
                    placeholder=_('Ce topic est verrouillé.'),
                    disabled=True
                )

    def clean(self):
        cleaned_data = super(PostForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_('Vous devez écrire une réponse !')])

        elif len(text) > settings.ZDS_APP['forum']['max_post_length']:
            self._errors['text'] = self.error_class(
                [_('Ce message est trop long, il ne doit pas dépasser {0} '
                   'caractères').format(settings.ZDS_APP['forum']['max_post_length'])])

        return cleaned_data


class MoveTopicForm(forms.Form):

    forum = forms.ModelChoiceField(
        label=_('Forum'),
        queryset=Forum.objects.all(),
        required=True,
    )

    def __init__(self, topic, *args, **kwargs):
        super(MoveTopicForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('topic-edit')
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'move-topic'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('forum'),
            Hidden('move', ''),
            Hidden('topic', topic.pk),
            StrictButton(_('Valider'), type='submit'),
        )
