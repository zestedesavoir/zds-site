#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from django import forms
from django.forms.extras.widgets import SelectDateWidget

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder

from zds.poll.models import Poll, Choice, UniqueVote, MultipleVote


class PollForm(forms.ModelForm):

    class Meta:
        model = Poll
        fields = ['title', 'anonymous_vote', 'unique_vote', 'enddate']
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
                ['Le champ titre ne peut être vide'])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        enddate = cleaned_data.get('enddate')

        if enddate < datetime.datetime.today():
            self._errors['enddate'] = self.error_class(
                ['La date ne peut pas être antérieure à aujourd\'hui'])
            if 'enddate' in cleaned_data:
                del cleaned_data['enddate']

        return cleaned_data


class ChoiceForm(forms.ModelForm):

    class Meta:
        model = Choice
        fields = ['choice']

    def clean(self):
        cleaned_data = super(ChoiceForm, self).clean()
        choice = cleaned_data.get('choice')

        if choice and choice.strip() == '':
            self._errors['choice'] = self.error_class(
                ['Le champ choix ne peut être vide'])
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
    extra=3,
    can_delete=False,
    can_order=False,
    min_num=2
)


class VoteForm(forms.ModelForm):

    def __init__(self, poll=None, *args, **kwargs):
        super(VoteForm, self).__init__(*args, **kwargs)
        self.fields['choice'].queryset = Choice.objects.filter(poll=poll)

        self.helper = FormHelper()

        self.helper.layout = Layout(
            'choice',
            ButtonHolder(
                StrictButton('Voter', type='submit'),
            ),
        )


class UniqueVoteForm(VoteForm):

    class Meta:
        model = UniqueVote
        fields = ('choice',)
        widgets = {
            'choice': forms.RadioSelect
        }


class MultipleVoteForm(VoteForm):
    # TODO pas fonctionnel, à finir
    class Meta:
        model = MultipleVote
        fields = ('choice',)

    choice = forms.ModelMultipleChoiceField(
        queryset=Choice.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
