# coding: utf-8

from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, ButtonHolder, Submit, Field, Hidden, Div
from crispy_forms.bootstrap import StrictButton
from zds.utils.models import SubCategory
from zds.utils.forms import CommonLayoutEditor


class ArticleForm(forms.Form):
    title = forms.CharField(
        label='Titre',
        max_length=80,
    )

    description = forms.CharField(
        max_length=200,
    )
    
    text = forms.CharField(
        label = 'Texte',
        required = False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )
    
    image = forms.ImageField(
        label='Selectionnez une image', 
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label = "Sous catégories de votre article",
        queryset = SubCategory.objects.all(),
        required = False
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
        self._errors['subcategory'] = None
        return super(ArticleForm, self).clean()

class ReactionForm(forms.Form):
    text = forms.CharField(
        label = '',
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre message au format Markdown.'
            }
        )
    )

    def __init__(self, article, user, *args, **kwargs):
        super(ReactionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.article.views.answer') + '?article=' + str(article.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_reaction', '{{ last_reaction_pk }}'),
        )

        if article.antispam(user):
            self.helper['text'].wrap(
                Field, 
                placeholder = u'Vous ne pouvez pas encore poster sur cet article (protection antispam de 15 min).',
                disabled = True
            )
        elif article.is_locked:
            self.helper['text'].wrap(
                Field, 
                placeholder = u'Cet article est verrouillé.',
                disabled = True
            )