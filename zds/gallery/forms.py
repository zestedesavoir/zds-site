# coding: utf-8

from django.conf import settings

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, \
    Field, ButtonHolder, Hidden
from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from zds.gallery.models import Gallery, Image


class GalleryForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=Gallery._meta.get_field('title').max_length,
    )

    subtitle = forms.CharField(
        label='Sous-titre',
        max_length=Gallery._meta.get_field('subtitle').max_length,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(GalleryForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'clearfix'
        self.helper.form_action = reverse('zds.gallery.views.new_gallery')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('subtitle'),
            ButtonHolder(
                StrictButton(u'Créer', type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(GalleryForm, self).clean()

        title = cleaned_data.get('title')

        if title and title.strip() == '':
            self._errors['title'] = self.error_class(
                [u'Le champ titre ne peut être vide'])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        return cleaned_data


class UserGalleryForm(forms.Form):
    user = forms.CharField(
        label='',
        max_length=User._meta.get_field('username').max_length,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Nom de l\'utilisateur',
                'data-autocomplete': '{ "type": "single" }'
            }
        )
    )

    mode = forms.ChoiceField(
        label='',
        choices=(
            ('R', "En mode lecture"),
            ('W', "En mode écriture"),
        ),
        required=True,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super(UserGalleryForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'clearfix'
        self.helper.form_action = reverse('zds.gallery.views.modify_gallery')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('user', autocomplete='off'),
            Field('mode'),
            Hidden('gallery', '{{ gallery.pk }}'),
            Hidden('adduser', 'True'),
            StrictButton('Ajouter', type='submit'),
        )

    def clean(self):
        cleaned_data = super(UserGalleryForm, self).clean()

        user = cleaned_data.get('user')

        if User.objects.filter(username=user).count() == 0:
            self._errors['user'] = self.error_class(
                [u'Ce nom d\'utilisateur n\'existe pas'])

        return cleaned_data


class ImageForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=Image._meta.get_field('title').max_length,
        required=True,
    )

    legend = forms.CharField(
        label=u'Légende',
        max_length=Image._meta.get_field('legend').max_length,
        required=False,
    )

    physical = forms.ImageField(
        label=u'Sélectionnez votre image',
        required=True,
        help_text='Taille maximum : {0} Ko'.format(settings.ZDS_APP['gallery']['image_max_size'] / 1024)
    )

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'clearfix'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('legend'),
            Field('physical'),
            ButtonHolder(
                StrictButton('Ajouter', type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(ImageForm, self).clean()

        physical = cleaned_data.get('physical')

        if physical is not None and physical.size > settings.ZDS_APP['gallery']['image_max_size']:
            self._errors['physical'] = self.error_class(
                [u'Votre image est trop lourde, la limite autorisée '
                 u'est de {0} Ko'.format(settings.ZDS_APP['gallery']['image_max_size'] / 1024)])
        return cleaned_data


class ArchiveImageForm(forms.Form):
    file = forms.FileField(
        label='Sélectionnez l\'archive contenant les images à charger',
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(ArchiveImageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'clearfix'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('file'),
            ButtonHolder(
                StrictButton('Importer', type='submit'),
                HTML('<a class="btn btn-cancel" '
                     u'href="{{ gallery.get_absolute_url }}">Annuler</a>'),
            ),
        )

    def clean(self):
        cleaned_data = super(ArchiveImageForm, self).clean()

        file = cleaned_data.get('file')
        extension = file.name.split('.')[-1]

        if extension != "zip":
            self._errors['file'] = self.error_class(
                [u"Le champ n'accepte que les fichiers zip"])
            if 'file' in cleaned_data:
                del cleaned_data['file']

        return cleaned_data


class UpdateImageForm(ImageForm):

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)

        self.fields['physical'].required = False

        self.helper = FormHelper()
        self.helper.form_class = 'clearfix'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('legend'),
            Field('physical'),
            ButtonHolder(
                StrictButton(u'Mettre à jour', type='submit'),
            ),
        )


class ImageAsAvatarForm(forms.Form):

    """"Form to add current image as avatar"""

    def __init__(self, *args, **kwargs):
        super(ImageAsAvatarForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'clearfix'
        self.helper.form_action = reverse('zds.member.views.update_avatar')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Hidden('avatar_url', '{{ image.physical.url }}'),
            ButtonHolder(
                StrictButton("Utiliser comme avatar", type='submit'),
            ),
        )
