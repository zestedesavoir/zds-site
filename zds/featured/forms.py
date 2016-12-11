# coding: utf-8

from datetime import datetime

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from zds.featured.models import FeaturedResource, FeaturedMessage


class FeaturedResourceForm(forms.ModelForm):
    class Meta:
        model = FeaturedResource

        fields = ['title', 'type', 'authors', 'image_url', 'url']

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': _(u'Titre de la Une')
                }
            ),

            'type': forms.TextInput(
                attrs={
                    'placeholder': _(u'ex: Un projet, Un article, Un tutoriel...')
                }
            ),

            'authors': forms.TextInput(
                attrs={
                    'placeholder': _(u'Des auteurs (ou pas) ?')
                }
            ),

            'image_url': forms.URLInput(
                attrs={
                    'placeholder': _(u'Lien vers l\'image de la Une (dimensions: 228x228px).')
                }
            ),

            'url': forms.URLInput(
                attrs={
                    'placeholder': _(u'Lien vers la ressource.')
                }
            )
        }

    pubdate = forms.DateField(
        label='Date de publication',
        widget=forms.DateInput(attrs={
            'class': 'date_picker_field'
        }),
    )

    pubtime = forms.TimeField(
        label='Heure de publication',
        widget=forms.TimeInput(format='%H:%M'),
        initial='07:00'
    )

    major_update = forms.BooleanField(
        label=_(u'Mise à jour majeure (fera passer la Une en première position lors d\'un changement)'),
        initial=False,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(FeaturedResourceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('featured-resource-create')

        self.helper.layout = Layout(
            Field('title'),
            Field('type'),
            Field('authors'),
            Field('image_url'),
            Field('url'),
            Field('major_update'),
            Field('pubdate'),
            Field('pubtime'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(FeaturedResourceForm, self).clean()

        if 'pubdate' not in cleaned_data or not cleaned_data['pubdate']:
            self._errors['pubdate'] = self.error_class([_(u'Vous devez fournir une date de publication !')])
        elif 'pubtime' not in cleaned_data or not cleaned_data['pubtime']:
            self._errors['pubtime'] = self.error_class([_(u'Vous devez fournir une heure de publication !')])
        else:
            date = cleaned_data['pubdate']
            time = cleaned_data['pubtime']

            publication_time = datetime(date.year, date.month, date.day, time.hour, time.minute)

            if publication_time < datetime.now():
                self.errors['pubdata'] = self.error_class([_(u'Vous ne pouvez pas publier dans le passé !')])
                del cleaned_data['pubdate']
            else:
                cleaned_data['pubdate'] = publication_time

            return cleaned_data


class FeaturedMessageForm(forms.ModelForm):
    class Meta:
        model = FeaturedMessage

        fields = ['hook', 'message', 'url']

        widgets = {
            'hook': forms.TextInput(
                attrs={
                    'placeholder': _(u'Mot d\'accroche court ("Nouveau !")')
                }
            ),

            'message': forms.TextInput(
                attrs={
                    'placeholder': _(u'Message à afficher')
                }
            ),

            'url': forms.URLInput(
                attrs={
                    'placeholder': _(u'Lien vers la description de la ressource')
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super(FeaturedMessageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('featured-message-create')

        self.helper.layout = Layout(
            Field('hook'),
            Field('message'),
            Field('url'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ),
        )
