# coding: utf-8

from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import Layout, ButtonHolder, Field, Div


class CommonLayoutEditor(Layout):

    def __init__(self, *args, **kwargs):
        super(
            CommonLayoutEditor,
            self).__init__(
            Div(
                Field(
                    'text',
                    css_class='md-editor'),
                ButtonHolder(
                    StrictButton(
                        'Envoyer',
                        type='submit',
                        css_class='submit tiny',
                        name='answer'),
                    StrictButton(
                        u'Aperçu',
                        type='submit',
                        css_class='submit tiny',
                        name='preview'),
                ),
            ),
        )


class CommonLayoutModalText(Layout):

    def __init__(self, *args, **kwargs):
        super(CommonLayoutModalText, self).__init__(
            Field('text'),
        )
