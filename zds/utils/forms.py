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


class TagValidator(object):
    """
    validate tags
    """
    def __init__(self):
        self.__errors = []
        self.logger = logging.getLogger("zds.utils.forms")

    def validate_raw_string(self, raw_string):
        if raw_string is None or not isinstance(raw_string, basestring):
            return self.validate_string_list([])
        return self.validate_string_list(raw_string.split(","))

    def validate_length(self, raw_string):
        if len(_) <= Tag._meta.get_field("title").max_length:
            self.errors.append(_(u"Le tag est trop long"))
            self.logger.debug("%s est trop long expected=%d got=%d", raw_string,
                              Tag._meta.get_field("title").max_length, len(raw_string))
            return False
        return True

    def validate_string_list(self, string_list):
        results = map(self.validate_length, string_list) + map(self.validate_utf8mb4, string_list)
        return all(results)

    def validate_utf8mb4(self, raw_string):
        if contains_utf8mb4(raw_string):
            self.errors.append(_(u"Le tag contient des caractères utf8mb4"))
            self.logger.warn("%s contains utf8mb4 char", raw_string)
            return False
        return True

    @property
    def errors(self):
        return self.__errors
