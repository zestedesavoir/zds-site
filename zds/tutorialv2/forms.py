# coding: utf-8
from django import forms
from django.conf import settings

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Submit, Field, ButtonHolder, Hidden
from django.core.urlresolvers import reverse

from zds.utils.forms import CommonLayoutModalText, CommonLayoutEditor, CommonLayoutVersionEditor
from zds.utils.models import SubCategory, Licence
from zds.tutorialv2.models import TYPE_CHOICES
from zds.utils.models import HelpWriting
from zds.tutorialv2.models.models_database import PublishableContent
from django.utils.translation import ugettext_lazy as _
from zds.member.models import Profile
from zds.tutorialv2.utils import slugify_raise_on_invalid, InvalidSlugError
from zds.utils.forms import TagValidator


class FormWithTitle(forms.Form):
    title = forms.CharField(
        label=_(u'Titre'),
        max_length=PublishableContent._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    def clean(self):
        cleaned_data = super(FormWithTitle, self).clean()

        title = cleaned_data.get('title')

        if title is not None and not title.strip():
            self._errors['title'] = self.error_class(
                [_(u'Le champ du titre ne peut être vide.')])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        try:
            slugify_raise_on_invalid(title)
        except InvalidSlugError as e:
            self._errors['title'] = self.error_class(
                [_(u"Ce titre n'est pas autorisé, son slug est invalide {} !").format(e if e.message else '')])

        return cleaned_data


class AuthorForm(forms.Form):

    username = forms.CharField(
        label=_(u"Auteurs à ajouter séparés d'une virgule."),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username'),
            ButtonHolder(
                StrictButton(_('Ajouter'), type='submit'),
            )
        )

    def clean_username(self):
        """Check every username and send it to the cleaned_data['user'] list

        :return: a dictionary of all treated data with the users key added
        """
        cleaned_data = super(AuthorForm, self).clean()
        users = []
        if cleaned_data.get('username'):
            for username in cleaned_data.get('username').split(','):
                user = Profile.objects.contactable_members().filter(user__username__iexact=username.strip().lower())\
                    .first()
                if user is not None:
                    users.append(user.user)
            if len(users) > 0:
                cleaned_data['users'] = users
        return cleaned_data

    def is_valid(self):
        return super(AuthorForm, self).is_valid() and 'users' in self.clean()


class RemoveAuthorForm(AuthorForm):

    def clean_username(self):
        """Check every username and send it to the cleaned_data['user'] list

        :return: a dictionary of all treated data with the users key added
        """
        cleaned_data = super(AuthorForm, self).clean()
        users = []
        for username in cleaned_data.get('username').split(','):
            # we can remove all users (bots inclued)
            user = Profile.objects.filter(user__username__iexact=username.strip().lower()).first()
            if user is not None:
                users.append(user.user)
        if len(users) > 0:
            cleaned_data['users'] = users
        return cleaned_data


class ContainerForm(FormWithTitle):

    introduction = forms.CharField(
        label=_(u'Introduction'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre introduction, au format Markdown.'),
                'class': 'md-editor preview-source'
            }
        )
    )

    conclusion = forms.CharField(
        label=_(u'Conclusion'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre conclusion, au format Markdown.'),
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u'Message de suivi'),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications.')
            }
        )
    )

    last_hash = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(ContainerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('introduction', css_class='md-editor preview-source'),
            ButtonHolder(StrictButton(_(u'Aperçu'), type='preview', name='preview',
                                      css_class='btn btn-grey preview-btn'),),
            HTML('{% if form.introduction.value %}{% include "misc/previsualization.part.html" \
            with text=form.introduction.value %}{% endif %}'),
            Field('conclusion', css_class='md-editor preview-source'),
            ButtonHolder(StrictButton(_(u'Aperçu'), type='preview', name='preview',
                                      css_class='btn btn-grey preview-btn'),),
            HTML('{% if form.conclusion.value %}{% include "misc/previsualization.part.html" \
            with text=form.conclusion.value %}{% endif %}'),
            Field('msg_commit'),
            Field('last_hash'),
            ButtonHolder(
                StrictButton(
                    _(u'Valider'),
                    type='submit'),
            )
        )


class ContentForm(ContainerForm):

    description = forms.CharField(
        label=_(u'Description'),
        max_length=PublishableContent._meta.get_field('description').max_length,
        required=False,
    )

    tags = forms.CharField(
        label=_(u'Tag(s) séparés par une virgule (exemple: python,django,web)'),
        max_length=64,
        required=False,
        widget=forms.TextInput(
            attrs={
                'data-autocomplete': '{ "type": "multiple", "fieldname": "title", "url": "/api/tags/?search=%s" }'
            }
        )
    )

    image = forms.ImageField(
        label=_(u'Sélectionnez le logo du contenu (max. {} Ko).').format(
            str(settings.ZDS_APP['gallery']['image_max_size'] / 1024)),
        required=False
    )

    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label=_(u'Sous catégories de votre contenu. Si aucune catégorie ne convient '
                u"n'hésitez pas à en demander une nouvelle lors de la validation !"),
        queryset=SubCategory.objects.order_by('title').all(),
        required=True,
        widget=forms.CheckboxSelectMultiple()
    )

    licence = forms.ModelChoiceField(
        label=(
            _(u'Licence de votre publication (<a href="{0}" alt="{1}">En savoir plus sur les licences et {2}</a>).')
            .format(
                settings.ZDS_APP['site']['licenses']['licence_info_title'],
                settings.ZDS_APP['site']['licenses']['licence_info_link'],
                settings.ZDS_APP['site']['litteral_name'],
            )
        ),
        queryset=Licence.objects.order_by('title').all(),
        required=True,
        empty_label=_('Choisir une licence')
    )

    helps = forms.ModelMultipleChoiceField(
        label=_(u"Pour m'aider, je cherche un... (non disponible pour les billets)"),
        queryset=HelpWriting.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        super(ContentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('tags'),
            Field('type'),
            Field('image'),
            Field('introduction', css_class='md-editor preview-source'),
            ButtonHolder(StrictButton(_(u'Aperçu'), type='preview', name='preview',
                                      css_class='btn btn-grey preview-btn'),),
            HTML('{% if form.introduction.value %}{% include "misc/previsualization.part.html" \
            with text=form.introduction.value %}{% endif %}'),
            Field('conclusion', css_class='md-editor preview-source'),
            ButtonHolder(StrictButton(_(u'Aperçu'), type='preview', name='preview',
                                      css_class='btn btn-grey preview-btn'),),
            HTML('{% if form.conclusion.value %}{% include "misc/previsualization.part.html" \
            with text=form.conclusion.value %}{% endif %}'),
            Field('last_hash'),
            Field('licence'),
            Field('subcategory', template='crispy/checkboxselectmultiple.html'),
            HTML(_(u"<p>Demander de l'aide à la communauté !<br>"
                   u"Si vous avez besoin d'un coup de main, "
                   u"sélectionnez une ou plusieurs catégories d'aide ci-dessous "
                   u'et votre contenu apparaîtra alors sur <a href='
                   u'"{% url "content:helps" %}" '
                   u'alt="aider les auteurs">la page d\'aide</a>.</p>')),
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

    def clean(self):
        cleaned_data = super(ContentForm, self).clean()
        image = cleaned_data.get('image')

        if image is not None and image.size > settings.ZDS_APP['gallery']['image_max_size']:
            self._errors['image'] = self.error_class(
                [_(u'Votre logo est trop lourd, la limite autorisée est de {} Ko')
                 .format(settings.ZDS_APP['gallery']['image_max_size'] / 1024)])
        validator = TagValidator()
        if not validator.validate_raw_string(cleaned_data.get('tags')):
            self._errors['tags'] = self.error_class(validator.errors)
        return cleaned_data


class ExtractForm(FormWithTitle):

    text = forms.CharField(
        label=_(u'Texte'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message, au format Markdown.')
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u'Message de suivi'),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications.')
            }
        )
    )

    last_hash = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('last_hash'),
            CommonLayoutVersionEditor(),
        )


class ImportForm(forms.Form):

    file = forms.FileField(
        label=_(u'Sélectionnez le contenu à importer.'),
        required=True
    )
    images = forms.FileField(
        label=_(u'Fichier zip contenant les images du contenu.'),
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
            ext = tuto.name.split('.')[-1]
            if ext != 'tuto':
                del cleaned_data['file']
                msg = _(u'Le fichier doit être au format .tuto.')
                self._errors['file'] = self.error_class([msg])

        if images is not None:
            ext = images.name.split('.')[-1]
            if ext != 'zip':
                del cleaned_data['images']
                msg = _(u'Le fichier doit être au format .zip.')
                self._errors['images'] = self.error_class([msg])


class ImportContentForm(forms.Form):

    archive = forms.FileField(
        label=_(u"Sélectionnez l'archive de votre contenu."),
        required=True
    )
    image_archive = forms.FileField(
        label=_(u"Sélectionnez l'archive des images."),
        required=False
    )

    msg_commit = forms.CharField(
        label=_(u'Message de suivi'),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications.')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ImportContentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('archive'),
            Field('image_archive'),
            Field('msg_commit'),
            ButtonHolder(
                StrictButton("Importer l'archive", type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(ImportContentForm, self).clean()

        # Check that the files extensions are correct
        archive = cleaned_data.get('archive')

        if archive is not None:
            ext = archive.name.split('.')[-1]
            if ext != 'zip':
                del cleaned_data['archive']
                msg = _(u"L'archive doit être au format .zip.")
                self._errors['archive'] = self.error_class([msg])

        image_archive = cleaned_data.get('image_archive')

        if image_archive is not None:
            ext = image_archive.name.split('.')[-1]
            if ext != 'zip':
                del cleaned_data['image_archive']
                msg = _(u"L'archive doit être au format .zip.")
                self._errors['image_archive'] = self.error_class([msg])

        return cleaned_data


class ImportNewContentForm(ImportContentForm):

    subcategory = forms.ModelMultipleChoiceField(
        label=_(u'Sous catégories de votre contenu. Si aucune catégorie ne convient '
                u"n'hésitez pas à en demander une nouvelle lors de la validation !"),
        queryset=SubCategory.objects.order_by('title').all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                'required': 'required',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ImportContentForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('archive'),
            Field('image_archive'),
            Field('subcategory'),
            Field('msg_commit'),
            ButtonHolder(
                StrictButton("Importer l'archive", type='submit'),
            ),
        )


class BetaForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput, required=True)

# Notes


class NoteForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message, au format Markdown.'),
                'required': 'required'
            }
        )
    )
    last_note = forms.IntegerField(
        label='',
        widget=forms.HiddenInput(),
        required=False
    )

    def __init__(self, content, reaction, *args, **kwargs):
        """initialize the form, handle antispam GUI
        :param content: the parent content
        :type content: zds.tutorialv2.models.models_database.PublishableContent
        :param reaction: the initial reaction if we edit, ``Ǹone```otherwise
        :type reaction: zds.tutorialv2.models.models_database.ContentReaction
        :param args:
        :param kwargs:
        """

        last_note = kwargs.pop('last_note', 0)

        super(NoteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:add-reaction') + u'?pk={}'.format(content.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Field('last_note') if not last_note else Hidden('last_note', last_note)
        )

        if content.antispam():
            if not reaction:
                self.helper['text'].wrap(
                    Field,
                    placeholder=_(u"Vous avez posté il n'y a pas longtemps. Merci de patienter "
                                  u'au moins 15 minutes entre deux messages consécutifs '
                                  u'afin de limiter le flood.'),
                    disabled=True)
        elif content.is_locked:
            self.helper['text'].wrap(
                Field,
                placeholder=_(u'Ce contenu est verrouillé.'),
                disabled=True
            )

        if reaction is not None:
            self.initial.setdefault('text', reaction.text)

        self.content = content

    def clean(self):
        cleaned_data = super(NoteForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u'Vous devez écrire une réponse !')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) > settings.ZDS_APP['forum']['max_post_length']:
            self._errors['text'] = self.error_class(
                [_(u'Ce message est trop long, il ne doit pas dépasser {0} '
                   u'caractères.').format(settings.ZDS_APP['forum']['max_post_length'])])
        last_note = cleaned_data.get('last_note', '0')
        if last_note is None:
            last_note = '0'
        is_valid = last_note == '0' or self.content.last_note is None or int(last_note) == self.content.last_note.pk
        if not is_valid:
            self._errors['last_note'] = self.error_class([_(u"Quelqu'un a posté pendant que vous répondiez")])
        return cleaned_data


class NoteEditForm(NoteForm):

    def __init__(self, *args, **kwargs):
        super(NoteEditForm, self).__init__(*args, **kwargs)

        content = kwargs['content']
        reaction = kwargs['reaction']

        self.helper.form_action = \
            reverse('content:update-reaction') + u'?message={}&pk={}'.format(reaction.pk, content.pk)


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
                'placeholder': _(u"Pour un contenu importé d'un autre site, adresse de la source.")
            }
        )
    )

    version = forms.CharField(widget=forms.HiddenInput(), required=True)

    previous_page_url = ''

    def __init__(self, content, *args, **kwargs):
        """

        :param content: the parent content
        :type content: zds.tutorialv2.models.models_database.PublishableContent
        :param args:
        :param kwargs:
        :return:
        """
        super(AskValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url() + '?version=' + content.current_version

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:ask', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'ask-validation'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('source'),
            Field('version'),
            StrictButton(
                _(u'Confirmer'),
                type='submit')
        )

    def clean(self):
        cleaned_data = super(AskValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u'Vous devez fournir un commentaire aux validateurs.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class AcceptValidationForm(forms.Form):

    validation = None

    text = forms.CharField(
        label='',
        required=True,
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
                'placeholder': _(u"Pour un contenu importé d'un autre site, adresse de la source.")
            }
        )
    )

    def __init__(self, validation, *args, **kwargs):
        """

        :param validation: the linked validation request object
        :type validation: zds.tutorialv2.models.models_database.Validation
        :param args:
        :param kwargs:
        :return:
        """

        # modal form, send back to previous page:
        self.previous_page_url = reverse(
            'content:view',
            kwargs={
                'pk': validation.content.pk,
                'slug': validation.content.slug
            }) + '?version=' + validation.version

        super(AcceptValidationForm, self).__init__(*args, **kwargs)

        # if content is already published, it's probably a minor change, so do not check `is_major`
        self.fields['is_major'].initial = not validation.content.sha_public

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:accept', kwargs={'pk': validation.pk})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'valid-publish'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('source'),
            Field('is_major'),
            StrictButton(_(u'Publier'), type='submit')
        )

    def clean(self):
        cleaned_data = super(AcceptValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u'Vous devez fournir un commentaire aux validateurs.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class CancelValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Pourquoi annuler la validation ?'),
                'rows': '4'
            }
        )
    )

    def __init__(self, validation, *args, **kwargs):
        super(CancelValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = reverse(
            'content:view',
            kwargs={
                'pk': validation.content.pk,
                'slug': validation.content.slug
            }) + '?version=' + validation.version

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:cancel', kwargs={'pk': validation.pk})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'cancel-validation'

        self.helper.layout = Layout(
            HTML('<p>Êtes-vous certain de vouloir annuler la validation de ce contenu ?</p>'),
            CommonLayoutModalText(),
            ButtonHolder(
                StrictButton(
                    _(u'Confirmer'),
                    type='submit'))
        )

    def clean(self):
        cleaned_data = super(CancelValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u"Merci de fournir une raison à l'annulation.")])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class RejectValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire de rejet.'),
                'rows': '6'
            }
        )
    )

    def __init__(self, validation, *args, **kwargs):
        """

        :param validation: the linked validation request object
        :type validation: zds.tutorialv2.models.models_database.Validation
        :param args:
        :param kwargs:
        :return:
        """
        super(RejectValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = reverse(
            'content:view',
            kwargs={
                'pk': validation.content.pk,
                'slug': validation.content.slug
            }) + '?version=' + validation.version

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:reject', kwargs={'pk': validation.pk})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'reject'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            ButtonHolder(
                StrictButton(
                    _(u'Rejeter'),
                    type='submit'))
        )

    def clean(self):
        cleaned_data = super(RejectValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u'Merci de fournir une raison au rejet.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class RevokeValidationForm(forms.Form):

    version = forms.CharField(widget=forms.HiddenInput())

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Pourquoi dépublier ce contenu ?'),
                'rows': '6'
            }
        )
    )

    def __init__(self, content, *args, **kwargs):
        super(RevokeValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:revoke', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'unpublish'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('version'),
            StrictButton(
                _(u'Dépublier'),
                type='submit')
        )

    def clean(self):
        cleaned_data = super(RevokeValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u'Veuillez fournir la raison de votre dépublication.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class JsFiddleActivationForm(forms.Form):

    js_support = forms.BooleanField(
        label='À cocher pour activer JSFiddle.',
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        super(JsFiddleActivationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:activate-jsfiddle')
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'js-activation'

        self.helper.layout = Layout(
            Field('js_support'),
            ButtonHolder(
                StrictButton(
                    _(u'Valider'),
                    type='submit'),),
            Hidden('pk', '{{ content.pk }}'), )

    def clean(self):
        cleaned_data = super(JsFiddleActivationForm, self).clean()
        if 'js_support' not in cleaned_data:
            cleaned_data['js_support'] = False
        if 'pk' in self.data and self.data['pk'].isdigit():
            cleaned_data['pk'] = int(self.data['pk'])
        else:
            cleaned_data['pk'] = 0
        return cleaned_data


class MoveElementForm(forms.Form):

    child_slug = forms.HiddenInput()
    container_slug = forms.HiddenInput()
    first_level_slug = forms.HiddenInput()
    moving_method = forms.HiddenInput()

    MOVE_UP = 'up'
    MOVE_DOWN = 'down'
    MOVE_AFTER = 'after'
    MOVE_BEFORE = 'before'

    def __init__(self, *args, **kwargs):
        super(MoveElementForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:move-element')
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('child_slug'),
            Field('container_slug'),
            Field('first_level_slug'),
            Field('moving_method'),
            Hidden('pk', '{{ content.pk }}'))


class WarnTypoForm(forms.Form):

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Expliquez la faute'),
                'rows': '3'
            }
        )
    )

    target = forms.CharField(widget=forms.HiddenInput(), required=False)
    version = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, content, targeted, public=True, *args, **kwargs):
        super(WarnTypoForm, self).__init__(*args, **kwargs)

        self.content = content
        self.targeted = targeted

        # modal form, send back to previous page if any:
        if public:
            self.previous_page_url = targeted.get_absolute_url_online()
        else:
            self.previous_page_url = targeted.get_absolute_url_beta()

        # add an additional link to send PM if needed
        type_ = _(u"l'article") if content.type == 'ARTICLE' else _(u'le tutoriel')

        if targeted.get_tree_depth() == 0:
            pm_title = _(u"J'ai trouvé une faute dans {} « {} ».").format(type_, targeted.title)
        else:
            pm_title = _(u"J'ai trouvé une faute dans le chapitre « {} ».").format(targeted.title)

        usernames = ''
        num_of_authors = content.authors.count()
        for index, user in enumerate(content.authors.all()):
            if index != 0:
                usernames += '&'
            usernames += 'username=' + user.username

        msg = _(u'<p>Pas assez de place ? <a href="{}?title={}&{}">Envoyez un MP {}</a> !</a>').format(
            reverse('mp-new'), pm_title, usernames, _(u"à l'auteur") if num_of_authors == 1 else _(u'aux auteurs')
        )

        version = content.sha_beta
        if public:
            version = content.sha_public

        # create form
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:warn-typo') + '?pk={}'.format(content.pk)
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'warn-typo-modal'
        self.helper.layout = Layout(
            Field('target'),
            Field('text'),
            HTML(msg),
            Hidden('pk', '{{ content.pk }}'),
            Hidden('version', version),
            ButtonHolder(StrictButton(_(u'Envoyer'), type='submit'))
        )

    def clean(self):
        cleaned_data = super(WarnTypoForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or not text.strip():
            self._errors['text'] = self.error_class(
                [_(u'Vous devez indiquer la faute commise.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class PublicationForm(forms.Form):

    """
    The publication form (used only for content without preliminary validation).
    """

    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Pour un contenu importé d\'un autre site, adresse de la source.')
            }
        )
    )

    def __init__(self, content, *args, **kwargs):
        super(PublicationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:publish', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'valid-publication'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('source'),
            HTML("<p>Ce billet sera publié directement et n'engage que vous.</p>"),
            StrictButton(_(u'Publier'), type='submit')
        )


class UnpublicationForm(forms.Form):

    version = forms.CharField(widget=forms.HiddenInput())

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Pourquoi dépublier ce contenu ?'),
                'rows': '6'
            }
        )
    )

    def __init__(self, content, *args, **kwargs):
        super(UnpublicationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:unpublish', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'unpublish'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('version'),
            StrictButton(
                _(u'Dépublier'),
                type='submit')
        )


class OpinionValidationForm(forms.Form):

    version = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, content, *args, **kwargs):
        super(OpinionValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:valid', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'valid-opinion'

        self.helper.layout = Layout(
            HTML("<p>Êtes-vous certain(e) de vouloir valider ce billet ? Il pourra maintenant être présent sur la page "
                 "d'accueil.</p>"),
            CommonLayoutModalText(),
            Field('version'),
            StrictButton(
                _(u'Valider'),
                type='submit')
        )


class PromoteOpinionToArticleForm(forms.Form):

    version = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, content, *args, **kwargs):
        super(PromoteOpinionToArticleForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:promote', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'promote-opinion'

        self.helper.layout = Layout(
            HTML("<p>Êtes-vous certain(e) de vouloir promouvoir ce billet en article ?</p>"),
            CommonLayoutModalText(),
            Field('version'),
            StrictButton(
                _(u'Valider'),
                type='submit')
        )
