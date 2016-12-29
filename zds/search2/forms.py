# coding: utf-8
from django import forms

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from django.utils.translation import ugettext_lazy as _


class SearchForm(forms.Form):
    q = forms.CharField(
        label='',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'type': 'search',
                'required': 'required',
                'placeholder': _(u'Recherche')
            }
        )
    )

    def __init__(self, *args, **kwargs):

        search_query = kwargs.pop('search_query', '') or ''

        super(SearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'search_form'
        self.helper.form_class = 'clearfix search-form'
        self.helper.form_method = 'get'

        self.helper.layout = Layout(
            HTML(self.fields['q'].widget.render('q', search_query)),
            StrictButton(_('Rechercher'), type='submit')
        )

    def clean(self):
        cleaned_data = super(SearchForm, self).clean()

        query = cleaned_data.get('q')

        if query is not None and not query.strip():
            self._errors['q'] = self.error_class([_(u'Le champ ne peut être vide.')])

            if 'q' in cleaned_data:
                del cleaned_data['q']

        return cleaned_data
