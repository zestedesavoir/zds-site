# coding: utf-8

from django import forms


class PrivateTopicForm(forms.Form):
    participants = forms.CharField()
    title = forms.CharField(max_length=80)
    subtitle = forms.CharField(max_length=255, required=False)
    text = forms.CharField(widget=forms.Textarea)


class PrivatePostForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)
