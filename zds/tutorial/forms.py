# coding: utf-8
from django import forms
from django.conf import settings

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Fieldset, Submit, Field, \
    ButtonHolder, Hidden
from django.core.urlresolvers import reverse

from zds.utils.forms import CommonLayoutModalText, CommonLayoutEditor, CommonLayoutVersionEditor
from zds.utils.models import SubCategory, Licence
from zds.tutorial.models import Tutorial, TYPE_CHOICES, HelpWriting
from django.utils.translation import ugettext_lazy as _


class FormWithTitle(forms.Form):
    title = forms.CharField(
        label=_(u'Titre'),
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
                [_(u'Le champ Titre ne peut être vide')])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        return cleaned_data


class TutorialForm(FormWithTitle):

    description = forms.CharField(
        label=_(u'Description'),
        max_length=Tutorial._meta.get_field('description').max_length,
        required=False,
    )

    image = forms.ImageField(
        label=_(u'Sélectionnez le logo du tutoriel (max. {} Ko)').format(
            str(settings.ZDS_APP['gallery']['image_max_size'] / 1024)),
        required=False
    )

    introduction = forms.CharField(
        label=_(u'Introduction'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    conclusion = forms.CharField(
        label=_('Conclusion'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label=_(u"Sous catégories de votre tutoriel. Si aucune catégorie ne convient "
                u"n'hésitez pas à en demander une nouvelle lors de la validation !"),
        queryset=SubCategory.objects.all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                'required': 'required',
            }
        )
    )

    licence = forms.ModelChoiceField(
        label=(
            _(u'Licence de votre publication (<a href="{0}" alt="{1}">En savoir plus sur les licences et {2}</a>)')
            .format(
                settings.ZDS_APP['site']['licenses']['licence_info_title'],
                settings.ZDS_APP['site']['licenses']['licence_info_link'],
                settings.ZDS_APP['site']['name']
            )
        ),
        queryset=Licence.objects.all(),
        required=True,
        empty_label=None
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
            }
        )
    )

    helps = forms.ModelMultipleChoiceField(
        label=_(u"Pour m'aider je cherche un..."),
        queryset=HelpWriting.objects.all(),
        required=False,
        widget=forms.SelectMultiple()
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
            Field('licence'),
            Field('subcategory'),
            HTML(_(u"<p>Demander de l'aide à la communauté !<br>"
                   u"Si vous avez besoin d'un coup de main,"
                   u"sélectionnez une ou plusieurs catégories d'aide ci-dessous "
                   u"et votre tutoriel apparaitra alors sur <a href="
                   u"\"{% url \"zds.tutorial.views.help_tutorial\" %}\" "
                   u"alt=\"aider les auteurs\">la page d'aide</a>.</p>")),
            Field('helps'),
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
        label=_(u"Introduction"),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    conclusion = forms.CharField(
        label=_(u"Conclusion"),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
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
                    _(u'Valider'),
                    type='submit'),
                StrictButton(
                    _(u'Ajouter et continuer'),
                    type='submit',
                    name='submit_continue'),
            )
        )


class ChapterForm(FormWithTitle):

    image = forms.ImageField(
        label=_(u'Selectionnez le logo du tutoriel '
                u'(max. {0} Ko)').format(str(settings.ZDS_APP['gallery']['image_max_size'] / 1024)),
        required=False
    )

    introduction = forms.CharField(
        label=_(u'Introduction'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    conclusion = forms.CharField(
        label=_(u'Conclusion'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
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
            # Field('image'),  # disable because not used yet
            Field('introduction', css_class='md-editor'),
            Field('conclusion', css_class='md-editor'),
            Field('msg_commit'),
            Hidden('last_hash', '{{ last_hash }}'),
            ButtonHolder(
                StrictButton(
                    _(u'Valider'),
                    type='submit'),
                StrictButton(
                    _(u'Ajouter et continuer'),
                    type='submit',
                    name='submit_continue'),
            ))


class EmbdedChapterForm(forms.Form):
    introduction = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    image = forms.ImageField(
        label=_(u'Sélectionnez une image'),
        required=False)

    conclusion = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    msg_commit = forms.CharField(
        label=_(u'Message de suivi'),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Fieldset(
                _(u'Contenu'),
                Field('image'),
                Field('introduction', css_class='md-editor'),
                Field('conclusion', css_class='md-editor'),
                Field('msg_commit'),
                Hidden('last_hash', '{{ last_hash }}'),
            ),
            ButtonHolder(
                Submit('submit', _(u'Valider'))
            )
        )
        super(EmbdedChapterForm, self).__init__(*args, **kwargs)


class ExtractForm(FormWithTitle):

    text = forms.CharField(
        label=_(u'Texte'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
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
        label=_(u'Sélectionnez le tutoriel à importer'),
        required=True
    )
    images = forms.FileField(
        label=_(u'Fichier zip contenant les images du tutoriel'),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('file'),
            Field('images'),
            Submit('import-tuto', _(u'Importer le .tuto')),
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
                msg = _(u'Le fichier doit être au format .tuto')
                self._errors['file'] = self.error_class([msg])

        if images is not None:
            ext = images.name.split(".")[-1]
            if ext != "zip":
                del cleaned_data['images']
                msg = _(u'Le fichier doit être au format .zip')
                self._errors['images'] = self.error_class([msg])


class ImportArchiveForm(forms.Form):

    file = forms.FileField(
        label=_(u"Sélectionnez l'archive de votre tutoriel"),
        required=True
    )

    tutorial = forms.ModelChoiceField(
        label=_(u"Tutoriel vers lequel vous souhaitez importer votre archive"),
        queryset=Tutorial.objects.none(),
        required=True
    )

    def __init__(self, user, *args, **kwargs):
        super(ImportArchiveForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.fields['tutorial'].queryset = Tutorial.objects.filter(authors__in=[user])

        self.helper.layout = Layout(
            Field('file'),
            Field('tutorial'),
            Submit('import-archive', _(u"Importer l'archive")),
        )


# Notes


class NoteForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.'),
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
                    placeholder=_(u'Vous venez de poster. Merci de patienter '
                                  u'au moins 15 minutes entre deux messages consécutifs '
                                  u'afin de limiter le flood.'),
                    disabled=True)
        elif tutorial.is_locked:
            self.helper['text'].wrap(
                Field,
                placeholder=_(u'Ce tutoriel est verrouillé.'),
                disabled=True
            )

    def clean(self):
        cleaned_data = super(NoteForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Vous devez écrire une réponse !')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) > settings.ZDS_APP['forum']['max_post_length']:
            self._errors['text'] = self.error_class(
                [_(u'Ce message est trop long, il ne doit pas dépasser {0} '
                   u'caractères').format(settings.ZDS_APP['forum']['max_post_length'])])

        return cleaned_data


# Validations.

class AskValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire pour votre demande.'),
                'rows': '3'
            }
        )
    )
    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'URL de la version originale')
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
                _(u'Confirmer'),
                type='submit'),
            Hidden('tutorial', '{{ tutorial.pk }}'),
            Hidden('version', '{{ version }}'), )


class ValidForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire de publication.'),
                'rows': '2'
            }
        )
    )
    is_major = forms.BooleanField(
        label=_(u'Version majeure ?'),
        required=False,
        initial=True
    )
    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'URL de la version originale')
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
            StrictButton(_(u'Publier'), type='submit'),
            Hidden('tutorial', '{{ tutorial.pk }}'),
            Hidden('version', '{{ version }}'),
        )


class RejectForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire de rejet.'),
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
                    _(u'Rejeter'),
                    type='submit'),),
            Hidden('tutorial', '{{ tutorial.pk }}'),
            Hidden('version', '{{ version }}'), )


class ActivJsForm(forms.Form):

    js_support = forms.BooleanField(
        label='Cocher pour activer JSFiddle',
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        super(ActivJsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.tutorial.views.activ_js')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('js_support'),
            ButtonHolder(
                StrictButton(
                    _(u'Valider'),
                    type='submit'),),
            Hidden('content', '{{ tutorial.pk }}'), )
