from django import forms
from django.conf import settings


class UserGalleryForm(forms.Form):
    user= forms.CharField('Membre', required=False)
    gallery = forms.CharField('Gallery', required=False)
    mode = forms.CharField('Mode', required=False)
    
class GalleryForm(forms.Form):
    title= forms.CharField(max_length=80)
    subtitle = forms.CharField(max_length=200, required=False)

class ImageForm(forms.Form):
    gallery = forms.CharField('Gallery', required=False)
    physical = forms.ImageField(
        label='Select an image',
        help_text='max. '+str(settings.IMAGE_MAX_SIZE)+' megabytes'
    , required=False)
    title = forms.CharField('Titre')
    legend = forms.CharField('Legende', required=False)