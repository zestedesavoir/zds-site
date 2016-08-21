#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.utils.translation import ugettext_lazy as _

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder

from zds.poll.models import Poll, Choice


class PollForm(forms.ModelForm):

    class Meta:
        model = Poll
        fields = ['title', 'anonymous_vote', 'end_date', 'type_vote']
        widgets = {
            'title': forms.TextInput(attrs={'required': 'required'}),
            'end_date': SelectDateWidget()
        }

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Field('title'),
            Field('anonymous_vote'),
            Field('unique_vote'),
            Field('end_date')
        )

    def clean(self):
        cleaned_data = super(PollForm, self).clean()

        title = cleaned_data.get('title')

        if title and title.strip() == '':
            self._errors['title'] = self.error_class(
                [_(u'Le champ titre ne peut être vide')])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        end_date = cleaned_data.get('end_date')

        if end_date is not None and end_date < datetime.datetime.today():
            self._errors['end_date'] = self.error_class(
                [_(u'La date ne peut pas être antérieure à aujourd\'hui')])
            if 'end_date' in cleaned_data:
                del cleaned_data['end_date']

        return cleaned_data


class UpdatePollForm(forms.ModelForm):

    class Meta:
        model = Poll
        fields = ('activate', 'end_date')
        widgets = {
            'end_date': SelectDateWidget()
        }

    def __init__(self, *args, **kwargs):
        super(UpdatePollForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field('end_date'),
            Field('activate'),
            ButtonHolder(
                StrictButton_(u'Éditer', type='submit'),
            ),
        )


class ChoiceForm(forms.ModelForm):

    class Meta:
        model = Choice
        fields = ['choice']

    def clean(self):
        cleaned_data = super(ChoiceForm, self).clean()
        choice = cleaned_data.get('choice')

        if choice and choice.strip() == '':
            self._errors['choice'] = self.error_class(
                [_(u'Le champ choix ne peut être vide')])
            if 'title' in cleaned_data:
                del cleaned_data['choice']

        return cleaned_data


class ChoiceFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ChoiceFormSetHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(
            Field('choice'),
        )
        self.render_required_fields = False
        self.form_tag = False


PollInlineFormSet = forms.inlineformset_factory(
    Poll,
    Choice,
    form=ChoiceForm,
    can_delete=False,
    can_order=False,
    extra=0,
    min_num=2,
    max_num=20
)
