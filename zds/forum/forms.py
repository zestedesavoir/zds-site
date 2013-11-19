# coding: utf-8

from django import forms


class TopicForm(forms.Form):
    title = forms.CharField(max_length=80)
    subtitle = forms.CharField(max_length=255, required=False)
    text = forms.CharField(widget=forms.Textarea)


class PostForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class AlertForm(forms.Form):
    text = forms.CharField()