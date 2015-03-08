# coding: utf-8
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder

from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from zds.news.models import News


class NewsForm(forms.ModelForm):
    class Meta:
        model = News

    title = forms.CharField(
        label=_(u'Titre'),
        max_length=News._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    type = forms.CharField(
        label=_(u'Type'),
        max_length=News._meta.get_field('type').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    authors = forms.CharField(
        label=_('Auteurs'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Les auteurs doivent être séparés par une virgule.'),
                'required': 'required',
                'data-autocomplete': '{ "type": "multiple" }'
            }
        )
    )

    image_url = forms.CharField(
        label='Image URL',
        max_length=News._meta.get_field('image_url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url de l\'image de la une.')
            }
        )
    )

    url = forms.CharField(
        label='URL',
        max_length=News._meta.get_field('url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url de la ressource.')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(NewsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('news-new')

        self.helper.layout = Layout(
            Field('title'),
            Field('type'),
            Field('authors'),
            Field('image_url'),
            Field('url'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ),
        )
