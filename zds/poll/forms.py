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
        fields = ['title', 'anonymous_vote', 'enddate', 'type_vote']
        widgets = {
            'title': forms.TextInput(attrs={'required': 'required'}),
            'enddate': SelectDateWidget()
        }

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Field('title'),
            Field('anonymous_vote'),
            Field('unique_vote'),
            Field('enddate')
        )

    def clean(self):
        cleaned_data = super(PollForm, self).clean()

        title = cleaned_data.get('title')

        if title and title.strip() == '':
            self._errors['title'] = self.error_class(
                [_(u'Le champ titre ne peut être vide')])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        enddate = cleaned_data.get('enddate')

        if enddate is not None and enddate < datetime.datetime.today():
            self._errors['enddate'] = self.error_class(
                [_(u'La date ne peut pas être antérieure à aujourd\'hui')])
            if 'enddate' in cleaned_data:
                del cleaned_data['enddate']

        return cleaned_data


class UpdatePollForm(forms.ModelForm):

    class Meta:
        model = Poll
        fields = ('activate', 'enddate')
        widgets = {
            'enddate': SelectDateWidget()
        }

    def __init__(self, *args, **kwargs):
        super(UpdatePollForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field('enddate'),
            Field('activate'),
            ButtonHolder(
                StrictButton('Editer', type='submit'),
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
