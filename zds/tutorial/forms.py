# coding: utf-8

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div
from crispy_forms_foundation.layout import Layout, Fieldset, Submit, Field, \
    ButtonHolder
from crispy_forms.bootstrap import StrictButton

from django import forms
from django.conf import settings

from zds.tutorial.models import TYPE_CHOICES
from zds.utils.models import Category, SubCategory, Licence


class TutorialForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80
    )

    description = forms.CharField(
        label = 'Description',
        max_length = 200,
        required = False,
    )
    
    image = forms.ImageField(
        label = 'Selectionnez le logo du tutoriel (max. '+str(settings.IMAGE_MAX_SIZE/1024)+' Ko)', 
        required = False
    )

    introduction = forms.CharField(
        label = 'Introduction',
        required=False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    conclusion = forms.CharField(
        label = 'Conclusion',
        required=False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )
    
    type = forms.ChoiceField(
        choices=TYPE_CHOICES
    )

    subcategory = forms.ModelMultipleChoiceField(
        label = "Sous-catégories de votre tuto",
        queryset = SubCategory.objects.all(),
        required = True,
    )
    
    licence = forms.ModelChoiceField(
        label = "Licence de votre publication",
        queryset = Licence.objects.all(),
        required = False,
    )

    def __init__(self, *args, **kwargs):
        super(TutorialForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('type'),
            Field('image'),
            Field('introduction', css_class = 'md-editor'),
            Field('conclusion', css_class = 'md-editor'),
            Field('subcategory'),
            Field('licence'),
            ButtonHolder(
                StrictButton('Valider', type = 'submit', css_class = 'btn-submit'),
            ),
        )


class PartForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80
    )

    introduction = forms.CharField(
        label = 'Introduction',
        required=False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    conclusion = forms.CharField(
        label = 'Conclusion',
        required=False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(PartForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('introduction'),
            Field('conclusion'),
            ButtonHolder(
                StrictButton('Valider', type = 'submit', css_class = 'btn-submit'),
            )
        )

class ChapterForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80
    )
    
    image = forms.ImageField(
        label='Selectionnez le logo du tutoriel (max. '+str(settings.IMAGE_MAX_SIZE/1024)+' Ko)', 
        required=False
    )

    introduction = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    conclusion = forms.CharField(
        label = 'Conclusion',
        required=False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ChapterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('image'),
            Field('introduction'),
            Field('conclusion'),
            ButtonHolder(
                StrictButton('Valider', type = 'submit', css_class = 'btn-submit'),
                StrictButton('Ajouter et continuer', type = 'submit_continue', css_class = 'btn-submit'),
            )
        )

class EmbdedChapterForm(forms.Form):
    introduction = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    image = forms.ImageField(
        label='Selectionnez une image', 
        required=False)

    conclusion = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Fieldset(
                u'Contenu',
                Field('image'),
                Field('introduction'),
                Field('conclusion')
            ),
            ButtonHolder(
                Submit('submit', 'Valider')
            )
        )
        super(EmbdedChapterForm, self).__init__(*args, **kwargs)


class ExtractForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80
    )

    text = forms.CharField(
        label = 'Texte',
        required=False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('text'),
            ButtonHolder(
                StrictButton('Valider', type = 'submit', css_class = 'btn-submit'),
            )
        )

class ImportForm(forms.Form):

    file = forms.FileField(
        label='Selectionnez le tutoriel à importer',
        required=False
    )
    images = forms.FileField(
        label='Fichier zip contenant les images du tutoriel',
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('file'),
            Field('images'),
            Submit('submit', 'Importer'),
        )
        super(ImportForm, self).__init__(*args, **kwargs)

class NoteForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class AlertForm(forms.Form):
    text = forms.CharField()
