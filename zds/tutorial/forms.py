# coding: utf-8

from django import forms
from django.conf import settings

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Field, \
    ButtonHolder, Hidden
from django.core.urlresolvers import reverse

from zds.tutorial.models import TYPE_CHOICES
from zds.utils.forms import CommonLayoutModalText, CommonLayoutEditor
from zds.utils.models import SubCategory, Licence
from zds.tutorial.models import Tutorial


class FormWithTitle(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=Tutorial._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    def clean(self):
        cleaned_data = super(FormWithTitle, self).clean()

        title = cleaned_data.get('title')

        if title is not None and title.strip() == '':
            self._errors['title'] = self.error_class(
                [u'Le champ Titre ne peut être vide'])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        return cleaned_data


class TutorialForm(FormWithTitle):

    description = forms.CharField(
        label='Description',
        max_length=Tutorial._meta.get_field('description').max_length,
        required=False,
    )

    image = forms.ImageField(
        label='Sélectionnez le logo du tutoriel (max. ' + str(settings.IMAGE_MAX_SIZE / 1024) + ' Ko)',
        required=False
    )

    introduction = forms.CharField(
        label='Introduction',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    conclusion = forms.CharField(
        label='Conclusion',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label="Sous-catégories de votre tuto",
        queryset=SubCategory.objects.all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                'required': 'required',
            }
        )
    )

    licence = forms.ModelChoiceField(
        label="Licence de votre publication",
        queryset=Licence.objects.all(),
        required=True,
        empty_label=None
    )

    def __init__(self, *args, **kwargs):
        super(TutorialForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('type'),
            Field('image'),
            Field('introduction', css_class='md-editor'),
            Field('conclusion', css_class='md-editor'),
            Hidden('last_hash', '{{ last_hash }}'),
            Field('subcategory'),
            Field('licence'),
            ButtonHolder(
                StrictButton('Valider', type='submit'),
            ),
        )

        if 'type' in self.initial:
            self.helper['type'].wrap(
                Field,
                disabled=True)


class PartForm(FormWithTitle):

    introduction = forms.CharField(
        label='Introduction',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    conclusion = forms.CharField(
        label='Conclusion',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(PartForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('introduction', css_class='md-editor'),
            Field('conclusion', css_class='md-editor'),
            Hidden('last_hash', '{{ last_hash }}'),
            ButtonHolder(
                StrictButton(
                    'Valider',
                    type='submit'),
                StrictButton(
                    'Ajouter et continuer',
                    type='submit',
                    name='submit_continue'),
            )
        )


class ChapterForm(FormWithTitle):

    image = forms.ImageField(
        label=u'Selectionnez le logo du tutoriel '
              u'(max. {0} Ko)'.format(str(settings.IMAGE_MAX_SIZE / 1024)),
        required=False
    )

    introduction = forms.CharField(
        label='Introduction',
        required=False,
        widget=forms.Textarea
    )

    conclusion = forms.CharField(
        label='Conclusion',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ChapterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('image'),
            Field('introduction', css_class='md-editor'),
            Field('conclusion', css_class='md-editor'),
            Hidden('last_hash', '{{ last_hash }}'),
            ButtonHolder(
                StrictButton(
                    'Valider',
                    type='submit'),
                StrictButton(
                    'Ajouter et continuer',
                    type='submit',
                    name='submit_continue'),
            ))


class EmbdedChapterForm(forms.Form):
    introduction = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    image = forms.ImageField(
        label='Sélectionnez une image',
        required=False)

    conclusion = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Fieldset(
                u'Contenu',
                Field('image'),
                Field('introduction', css_class='md-editor'),
                Field('conclusion', css_class='md-editor'),
                Hidden('last_hash', '{{ last_hash }}'),
            ),
            ButtonHolder(
                Submit('submit', 'Valider')
            )
        )
        super(EmbdedChapterForm, self).__init__(*args, **kwargs)


class ExtractForm(FormWithTitle):

    text = forms.CharField(
        label='Texte',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Hidden('last_hash', '{{ last_hash }}'),
            CommonLayoutEditor()
        )


class ImportForm(forms.Form):

    file = forms.FileField(
        label='Sélectionnez le tutoriel à importer',
        required=False
    )
    images = forms.FileField(
        label='Fichier zip contenant les images du tutoriel',
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('file'),
            Field('images'),
            Submit('submit', 'Importer'),
        )
        super(ImportForm, self).__init__(*args, **kwargs)

# Notes


class NoteForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.',
                'required': 'required'
            }
        )
    )

    def __init__(self, tutorial, user, *args, **kwargs):
        super(NoteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'zds.tutorial.views.answer') + '?tutorial=' + str(tutorial.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_note', '{{ last_note_pk }}'),
        )

        if tutorial.antispam(user):
            if 'text' not in self.initial:
                self.helper['text'].wrap(
                    Field,
                    placeholder=u'Vous venez de poster. Merci de patienter '
                    u'au moins 15 minutes entre deux messages consécutifs '
                    u'afin de limiter le flood.',
                    disabled=True)
        elif tutorial.is_locked:
            self.helper['text'].wrap(
                Field,
                placeholder=u'Ce tutoriel est verrouillé.',
                disabled=True
            )

    def clean(self):
        cleaned_data = super(NoteForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [u'Vous devez écrire une réponse !'])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) > settings.MAX_POST_LENGTH:
            self._errors['text'] = self.error_class(
                [(u'Ce message est trop long, il ne doit pas dépasser {0} '
                  u'caractères').format(settings.MAX_POST_LENGTH)])

        return cleaned_data


# Validations.

class AskValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Commentaire pour votre demande.'
            }
        )
    )
    source = forms.CharField(
        label='Source originale',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Url de la version originale'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(AskValidationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.tutorial.views.ask_validation')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(), 
            Field('source'),
            StrictButton(
                'Confirmer',
                type='submit'),
            Hidden('tutorial', '{{ tutorial.pk }}'), 
            Hidden('version', '{{ version }}'), )


class ValidForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Commentaire de publication.'
            }
        )
    )
    is_major = forms.BooleanField(
        label='Version majeure ?',
        required=False,
        initial=True
    )
    source = forms.CharField(
        label='Source originale',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Url de la version originale'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ValidForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.tutorial.views.valid_tutorial')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('source'),
            Field('is_major'),
            StrictButton('Publier', type='submit'),
            Hidden('tutorial', '{{ tutorial.pk }}'),
            Hidden('version', '{{ version }}'),
        )


class RejectForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Commentaire de rejet.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(RejectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.tutorial.views.reject_tutorial')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            ButtonHolder(
                StrictButton(
                    'Rejeter',
                    type='submit'),),
            Hidden('tutorial', '{{ tutorial.pk }}'),
            Hidden('version', '{{ version }}'), )
