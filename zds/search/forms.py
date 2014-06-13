# encoding: utf-8

from django import forms
from haystack.forms import ModelSearchForm, model_choices


class CustomSearchForm(ModelSearchForm):
    def __init__(self, *args, **kwargs):
        super(CustomSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.MultipleChoiceField(
              choices=model_choices(), 
              required=False, 
              label='Rechercher dans', 
              widget=forms.CheckboxSelectMultiple(
                attrs={
                  'form': 'search_form'
                }
              )
          )