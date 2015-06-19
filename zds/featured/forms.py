# coding: utf-8
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

    title = forms.CharField(
        label=_(u'Titre'),
        max_length=FeaturedResource._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    type = forms.CharField(
        label=_(u'Type'),
        max_length=FeaturedResource._meta.get_field('type').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'ex: Un projet, un article, un tutoriel...'),
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
        max_length=FeaturedResource._meta.get_field('image_url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url de l\'image de la une (dimensions: 228x228).')
            }
        )
    )

    url = forms.CharField(
        label='URL',
        max_length=FeaturedResource._meta.get_field('url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers l\'url de la ressource.')
            }
        )
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
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ),
        )


class FeaturedMessageForm(forms.ModelForm):
    class Meta:
        model = FeaturedMessage

        fields = ['hook', 'message', 'url']

        widgets = {
            'hook': forms.TextInput(
                attrs={
                    'placeholder': _(u'Mesage d\'accroche court ("Nouveau !")')
                }
            ),

            'message': forms.TextInput(
                attrs={
                    'placeholder': _(u'Information à transmettre')
                }
            ),

            'url': forms.TextInput(
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
