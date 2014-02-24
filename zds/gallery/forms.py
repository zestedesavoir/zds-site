# coding: utf-8

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder, Submit,\
    Reset, HTML

class UserGalleryForm(forms.Form):
    user= forms.CharField('Membre', required=False)
    gallery = forms.CharField('Gallery', required=False)
    mode = forms.CharField('Mode', required=False)
    
class GalleryForm(forms.Form):
    title = forms.CharField(
        label = 'Titre',
        max_length=80
    )

    subtitle = forms.CharField(
        label = 'Sous-titre',
        max_length=200,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(GalleryForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_action = reverse('zds.gallery.views.new_gallery')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('subtitle'),
            ButtonHolder(
                Submit('submit', u'Créer'),
                Reset('reset', u'Réinitialiser'),
                HTML('<a class="btn btn-submit" href="{% url "zds.gallery.views.gallery_list" %}">Annuler</a>'),
            ),
        )

class ImageForm(forms.Form):
    gallery = forms.CharField('Gallery', required=False)
    physical = forms.ImageField(
        label='Select an image',
        help_text='max. '+str(settings.IMAGE_MAX_SIZE)+' megabytes'
    , required=False)
    title = forms.CharField('Titre')
    legend = forms.CharField('Legende', required=False)