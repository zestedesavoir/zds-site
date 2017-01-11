# coding: utf-8
import os
import random

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from zds.settings import BASE_DIR

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django.core.urlresolvers import reverse


class SearchForm(forms.Form):
    q = forms.CharField(
        label=_(u'Recherche'),
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'type': 'search',
                'required': 'required'
            }
        )
    )

    models = forms.MultipleChoiceField(
        label='',
        widget=forms.CheckboxSelectMultiple,
        required=False,
        choices=settings.ZDS_APP['search']['indexables']
    )

    def __init__(self, *args, **kwargs):

        super(SearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'search-form'
        self.helper.form_class = 'clearfix'
        self.helper.form_method = 'get'
        self.helper.form_action = reverse('search:query')

        try:
            with open(os.path.join(BASE_DIR, 'suggestions.txt'), 'r') as suggestions_file:
                suggestions = ', '.join(random.sample(suggestions_file.readlines(), 5)) + u'…'
        except IOError:
            suggestions = _(u'Mathématiques, Droit, UDK, Langues, Python…')

        self.fields['q'].widget.attrs['placeholder'] = suggestions

        self.helper.layout = Layout(
            Field('q'),
            StrictButton('', type='submit', css_class='ico-after ico-search', title=_(u'Rechercher'))
        )
