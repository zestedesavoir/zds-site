# coding: utf-8

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Hidden
from django import forms
from django.core.urlresolvers import reverse

from zds.article.models import Article
from zds.utils.forms import CommonLayoutEditor
from zds.utils.models import SubCategory


class ArticleForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=Article._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    description = forms.CharField(
        max_length=Article._meta.get_field('description').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    text = forms.CharField(
        label='Texte',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.',
                'required': 'required',
            }
        )
    )

    image = forms.ImageField(
        label='Selectionnez une image',
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label="Sous catégories de votre article",
        queryset=SubCategory.objects.all(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title', autocomplete='off'),
            Field('description', autocomplete='off'),
            Field('image'),
            Field('subcategory'),
            CommonLayoutEditor(),
        )

    def clean(self):
        cleaned_data = super(ArticleForm, self).clean()

        title = cleaned_data.get('title')
        description = cleaned_data.get('description')
        text = cleaned_data.get('text')

        if title is not None and title.strip() == '':
            self._errors['title'] = self.error_class(
                [u'Le champ Titre ne peut être vide'])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        if description is not None and description.strip() == '':
            self._errors['description'] = self.error_class(
                [u'Le champ Description ne peut être vide'])
            if 'description' in cleaned_data:
                del cleaned_data['description']

        if text is not None and text.strip() == '':
            self._errors['text'] = self.error_class(
                [u'Le champ Texte ne peut être vide'])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class ReactionForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre message au format Markdown.',
                'required': 'required'
            }
        )
    )

    def __init__(self, article, user, *args, **kwargs):
        super(ReactionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'zds.article.views.answer') + '?article=' + str(article.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_reaction', '{{ last_reaction_pk }}'),
        )

        if article.antispam(user):
            if 'text' not in self.initial:
                self.helper['text'].wrap(
                    Field,
                    placeholder=u'Vous ne pouvez pas encore poster u\
                    usur cet article (protection antispam de 15 min).',
                    disabled=True)
        elif article.is_locked:
            self.helper['text'].wrap(
                Field,
                placeholder=u'Cet article est verrouillé.',
                disabled=True
            )
