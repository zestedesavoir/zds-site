# coding: utf-8

from django import forms
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Submit, Field
from .models import Category, Plateform, Technology, BPlan


class ProjectForm(forms.Form):
    
    title = forms.CharField(
        label='Titre',
        max_length=80
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea
    )
    
    image = forms.ImageField(
        label='Selectionnez l\'image du projet (max. '+str(settings.IMAGE_MAX_SIZE/1024)+' Ko) ',
        required=False)
    
    categories = forms.ModelMultipleChoiceField(
        label = "Catégories du projet",
        queryset=Category.objects.all(),
        required = False,
    )
    technologies = forms.ModelMultipleChoiceField(
        label = "Technologies utilisées dans le projet",
        queryset=Technology.objects.all(),
        required = False,
    )
    plateforms = forms.ModelMultipleChoiceField(
        label = "Plateformes cible du projet",
        queryset=Plateform.objects.all(),
        required = False,
    ) 

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            
            Field('title'),
            Field('description'),
            Field('image'),
            Field('categories'),
            Field('technologies'),
            Field('plateforms'),
            Submit('submit', 'Valider'),
        )
        super(ProjectForm, self).__init__(*args, **kwargs)

class ProjectDetailsForm(forms.Form):
    
    short_description = forms.CharField(
        label='Description courte du projet',
        widget=forms.Textarea
    )

    long_description = forms.CharField(
        label='Description longue du projet',
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            
            Field('short_description'),
            Field('long_description'),
            Submit('submit', 'Valider'),
        )
        super(ProjectDetailsForm, self).__init__(*args, **kwargs)

class ProjectStrategyForm(forms.Form):
    
    strategy = forms.CharField(
        label='Cible clientèle',
        required=False,
        widget=forms.Textarea
    )

    product = forms.CharField(
        label='Votre Produit (Spécificités et Innovations)',
        required=False,
        widget=forms.Textarea
    )
    
    pricing = forms.CharField(
        label='Vos prix (Business model, licence)',
        required=False,
        widget=forms.Textarea
    )
    
    promote = forms.CharField(
        label='Plan de communication',
        required=False,
        widget=forms.Textarea
    )
    
    place = forms.CharField(
        label='Plan de distribution',
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            
            Field('product'),
            Field('pricing'),
            Field('promote'),
            Field('place'),
            Field('strategy'),
            Submit('submit', 'Valider'),
        )
        super(ProjectStrategyForm, self).__init__(*args, **kwargs)

class ProjectMarketStudyForm(forms.Form):
    
    market_study = forms.CharField(
        label='Rapport de votre étude de marché/faisabilité',
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('market_study'),
            Submit('submit', 'Valider'),
        )
        super(ProjectMarketStudyForm, self).__init__(*args, **kwargs)
        
class ProjectRoadmapForm(forms.Form):
    
    roadmap = forms.CharField(
        label='Votre roadmap (fonctionnalités et évolutions prévues)',
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('roadmap'),
            Submit('submit', 'Valider'),
        )
        super(ProjectRoadmapForm, self).__init__(*args, **kwargs)
