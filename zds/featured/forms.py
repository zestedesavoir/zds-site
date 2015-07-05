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
