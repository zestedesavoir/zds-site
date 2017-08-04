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

    pubdate = forms.DateTimeField(
        label=_(u'Date de publication'),
        input_formats=[
            '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M', '%Y-%m-%d', '%d/%m/%Y'],
        widget=forms.DateTimeInput(
            attrs={'placeholder': _(u'Exemple : 25/12/2016 10:00')},
            format='%d/%m/%Y %H:%M:%S'
        )
    )

    def __init__(self, *args, **kwargs):
        hide_major_update_field = kwargs.pop('hide_major_update_field', False)

        super(FeaturedResourceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('featured-resource-create')

        fields = [
            Field('title'),
            Field('type'),
            Field('authors'),
            Field('image_url'),
            Field('url')
        ]

        if not hide_major_update_field:
            fields.append(Field('major_update'))

        fields.extend([
            Field('pubdate'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            )
        ])

        self.helper.layout = Layout(*fields)


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
