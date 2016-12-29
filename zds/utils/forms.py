# coding: utf-8
import logging

from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import Layout, ButtonHolder, Field, Div, HTML
from django.utils.translation import ugettext_lazy as _
from zds.utils.models import Tag
from zds.utils.misc import contains_utf8mb4
# for compat with py3
try:
    assert isinstance("", basestring)
except (NameError, AssertionError):
    basestring = str


class CommonLayoutEditor(Layout):

    def __init__(self, *args, **kwargs):
        super(CommonLayoutEditor, self).__init__(
            Field('text', css_class='md-editor'),
            HTML("<div class='message-bottom'>"),
            HTML("<div class='message-submit'>"),
            StrictButton(
                _(u'Envoyer'),
                type='submit',
                name='answer'),
            StrictButton(
                _(u'Aperçu'),
                type='submit',
                name='preview',
                css_class='btn-grey',
                data_ajax_input='preview-message'),
            HTML("</div>"),
            HTML("</div>"),
            *args, **kwargs
        )


class CommonLayoutVersionEditor(Layout):

    def __init__(self, *args, **kwargs):
        super(CommonLayoutVersionEditor, self).__init__(
            Div(
                Field('text', css_class='md-editor'),
                Field('msg_commit'),
                ButtonHolder(
                    StrictButton(
                        _(u'Envoyer'),
                        type='submit',
                        name='answer'),
                    StrictButton(
                        _(u'Aperçu'),
                        type='submit',
                        name='preview',
                        css_class='btn-grey'),
                ),
            ),
            *args, **kwargs
        )


class CommonLayoutModalText(Layout):

    def __init__(self, *args, **kwargs):
        super(CommonLayoutModalText, self).__init__(
            Field('text'),
            *args, **kwargs
        )
