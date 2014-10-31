# coding: utf-8
from django import forms
from django.conf import settings

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Field, \
    ButtonHolder, Hidden
from django.core.urlresolvers import reverse

from zds.tutorial.models import TYPE_CHOICES
from zds.utils.forms import CommonLayoutModalText, CommonLayoutEditor, CommonLayoutVersionEditor
from zds.utils.models import SubCategory, Licence
from zds.tutorial.models import PubliableContent


class FormWithTitle(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=PubliableContent._meta.get_field('title').max_length,
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
        max_length=PubliableContent._meta.get_field('description').max_length,
        required=False,
    )

    image = forms.ImageField(
        label='Sélectionnez le logo du tutoriel (max. ' +
              str(settings.ZDS_APP['gallery']['image_max_size'] / 1024) +
              ' Ko)',
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
        label=u"Sous catégories de votre tutoriel. Si aucune catégorie ne convient "
              u"n'hésitez pas à en demander une nouvelle lors de la validation !",
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

    msg_commit = forms.CharField(
        label='Message de suivi',
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Un résumé de vos ajouts et modifications'
            }
        )
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
            Field('msg_commit'),
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

    msg_commit = forms.CharField(
        label='Message de suivi',
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Un résumé de vos ajouts et modifications'
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
            Field('msg_commit'),
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
              u'(max. {0} Ko)'.format(str(settings.ZDS_APP['gallery']['image_max_size'] / 1024)),
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

    msg_commit = forms.CharField(
        label='Message de suivi',
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Un résumé de vos ajouts et modifications'
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
            Field('msg_commit'),
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

    msg_commit = forms.CharField(
        label='Message de suivi',
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Un résumé de vos ajouts et modifications'
            }
        )
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
                Field('msg_commit'),
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

    msg_commit = forms.CharField(
        label='Message de suivi',
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Un résumé de vos ajouts et modifications'
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
            CommonLayoutVersionEditor(),
        )


class ImportForm(forms.Form):

    file = forms.FileField(
        label='Sélectionnez le tutoriel à importer',
        required=True
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
            Submit('import-tuto', 'Importer le .tuto'),
        )
        super(ImportForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ImportForm, self).clean()

        # Check that the files extensions are correct
        tuto = cleaned_data.get('file')
        images = cleaned_data.get('images')

        if tuto is not None:
            ext = tuto.name.split(".")[-1]
            if ext != "tuto":
                del cleaned_data['file']
                msg = u'Le fichier doit être au format .tuto'
                self._errors['file'] = self.error_class([msg])

        if images is not None:
            ext = images.name.split(".")[-1]
            if ext != "zip":
                del cleaned_data['images']
                msg = u'Le fichier doit être au format .zip'
                self._errors['images'] = self.error_class([msg])


class ImportArchiveForm(forms.Form):

    file = forms.FileField(
        label='Sélectionnez l\'archive de votre tutoriel',
        required=True
    )

    tutorial = forms.ModelChoiceField(
        label="Tutoriel vers lequel vous souhaitez importer votre archive",
        queryset=PubliableContent.objects.none(),
        required=True
    )

    def __init__(self, user, *args, **kwargs):
        super(ImportArchiveForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.fields['tutorial'].queryset = PubliableContent.objects.filter(authors__in=[user])

        self.helper.layout = Layout(
            Field('file'),
            Field('tutorial'),
            Submit('import-archive', 'Importer l\'archive'),
        )


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

        elif len(text) > settings.ZDS_APP['forum']['max_post_length']:
            self._errors['text'] = self.error_class(
                [(u'Ce message est trop long, il ne doit pas dépasser {0} '
                  u'caractères').format(settings.ZDS_APP['forum']['max_post_length'])])

        return cleaned_data


# Validations.

class AskValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Commentaire pour votre demande.',
                'rows': '3'
            }
        )
    )
    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'URL de la version originale'
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
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Commentaire de publication.',
                'rows': '2'
            }
        )
    )
    is_major = forms.BooleanField(
        label='Version majeure ?',
        required=False,
        initial=True
    )
    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'URL de la version originale'
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
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Commentaire de rejet.',
                'rows': '6'
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
