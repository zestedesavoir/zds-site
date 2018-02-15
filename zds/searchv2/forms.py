import os
import random

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django.core.urlresolvers import reverse


class SearchForm(forms.Form):
    q = forms.CharField(
        label=_('Recherche'),
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'type': 'search',
                'required': 'required'
            }
        )
    )

    choices = sorted(
        [(k, v[0]) for k, v in settings.ZDS_APP['search']['search_groups'].items()],
        key=lambda pair: pair[1]
    )

    models = forms.MultipleChoiceField(
        label='',
        widget=forms.CheckboxSelectMultiple,
        required=False,
        choices=choices
    )

    category = forms.CharField(widget=forms.HiddenInput, required=False)
    subcategory = forms.CharField(widget=forms.HiddenInput, required=False)
    from_library = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):

        super(SearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'search-form'
        self.helper.form_class = 'clearfix'
        self.helper.form_method = 'get'
        self.helper.form_action = reverse('search:query')

        try:
            with open(os.path.join(settings.BASE_DIR, 'suggestions.txt'), 'r') as suggestions_file:
                suggestions = ', '.join(random.sample(suggestions_file.readlines(), 5)) + '…'
        except OSError:
            suggestions = _('Mathématiques, Droit, UDK, Langues, Python…')

        self.fields['q'].widget.attrs['placeholder'] = suggestions

        self.helper.layout = Layout(
            Field('q'),
            StrictButton('', type='submit', css_class='ico-after ico-search', title=_('Rechercher')),
            Field('category'),
            Field('subcategory'),
            Field('from_library')
        )
