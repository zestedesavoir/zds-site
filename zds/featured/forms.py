# coding: utf-8
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from zds.featured.models import ResourceFeatured, MessageFeatured


class ResourceFeaturedForm(forms.ModelForm):
    class Meta:
        model = ResourceFeatured

    title = forms.CharField(
        label=_(u'Titre'),
        max_length=ResourceFeatured._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    type = forms.CharField(
        label=_(u'Type'),
        max_length=ResourceFeatured._meta.get_field('type').max_length,
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
        max_length=ResourceFeatured._meta.get_field('image_url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url de l\'image de la une.')
            }
        )
    )

    url = forms.CharField(
        label='URL',
        max_length=ResourceFeatured._meta.get_field('url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url de la ressource.')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ResourceFeaturedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('featured-create')

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


class MessageFeaturedForm(forms.ModelForm):
    class Meta:
        model = MessageFeatured

    message = forms.CharField(
        label=_(u'Message'),
        max_length=MessageFeatured._meta.get_field('message').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    url = forms.CharField(
        label=_(u'URL'),
        max_length=MessageFeatured._meta.get_field('url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url du message.'),
                'required': 'required',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(MessageFeaturedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('featured-message-create')

        self.helper.layout = Layout(
            Field('message'),
            Field('url'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ),
        )
