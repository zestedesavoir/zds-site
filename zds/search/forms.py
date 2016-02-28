from django import forms
from haystack import connections
from haystack.constants import DEFAULT_ALIAS
from haystack.forms import ModelSearchForm
from zds.search.constants import MODEL_NAMES


class CustomSearchForm(ModelSearchForm):

    def __init__(self, *args, **kwargs):
        super(CustomSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.MultipleChoiceField(
            choices=self.model_choices(),
            required=False,
            label='Rechercher dans',
            widget=forms.CheckboxSelectMultiple(
                  attrs={
                      'form': 'search_form'
                  }
            )
        )

    def model_choices(self, using=DEFAULT_ALIAS):
        choices = [
            ("%s.%s" %
             (m._meta.app_label,
              m._meta.model_name),
                self.get_model_name(
                 m._meta.app_label,
                 m._meta.model_name,
                 True)) for m in connections[using].get_unified_index().get_indexed_models()]
        return sorted(choices, key=lambda x: x[1])

    def get_model_name(self, app_label, module_name, plural):
        return MODEL_NAMES[app_label][module_name][plural]
