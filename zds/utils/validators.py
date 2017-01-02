# -*- coding: utf-8 -*-
import logging

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from zds.api.validators import Validator
from zds.member.models import Profile
from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import Layout, ButtonHolder, Field, Div, HTML
from django.utils.translation import ugettext_lazy as _
from zds.utils.models import Tag
from zds.utils.misc import contains_utf8mb4

class TitleValidator(Validator):
    """
    Validates title field of a Comment.
    """

    def validate_title(self, value):
        """
        Checks about title.

        :param value: title value
        :return: title value
        """
        msg = None
        if value:
            if value.strip() == '':
                msg = _(u'Le champ titre ne peut être vide.')
            if msg is not None:
                self.throw_error('title', msg)
        return value
        
        
class TextValidator(Validator):
    """
    Validates text field of a MP.
    """

    def validate_text(self, value):
        """
        Checks about text.

        :param value: text value
        :return: text value
        """
        msg = None
        if value:
            if value.strip() == '':
                msg = _(u'Le champ text ne peut être vide.')
            if msg is not None:
                self.throw_error('text', msg)
        return value


class TagValidator(object):
    """
    validate tags
    """
    def __init__(self):
        self.__errors = []
        self.logger = logging.getLogger("zds.utils.forms")
        self.__clean = []

    def validate_raw_string(self, raw_string):
        """
        validate a string composed as ``tag1,tag2``.

        :param raw_string: the string to be validate. If ``None`` this is considered as a empty str
        :type raw_string: basestring
        :return: ``True`` if ``raw_string`` is fully valid, ``False`` if at least one error appears. See ``self.errors``
        to get all internationalized error.
        """
        if raw_string is None or not isinstance(raw_string, basestring):
            return self.validate_string_list([])
        return self.validate_string_list(raw_string.split(","))

    def validate_length(self, tag):
        """
        Check the length is in correct range. See ``Tag.label`` max length to have the true upper bound.

        :param tag: the tag lavel to validate
        :return: ``True`` if length is valid
        """
        if len(tag) > Tag._meta.get_field("title").max_length:
            self.errors.append(_(u"Le tag {} est trop long (maximum {} caractères)".format(
                tag, Tag._meta.get_field("title").max_length)))
            self.logger.debug("%s est trop long expected=%d got=%d", tag,
                              Tag._meta.get_field("title").max_length, len(tag))
            return False
        return True

    def validate_string_list(self, string_list):
        """
        Same as ``validate_raw_string`` but with a list of tag labels.

        :param string_list:
        :return: ``True`` if ``v`` is fully valid, ``False`` if at least one error appears. See ``self.errors``
        to get all internationalized error.
        """
        self.__clean = list(filter(self.validate_length, string_list))
        self.__clean = list(filter(self.validate_utf8mb4, self.__clean))
        return len(string_list) == len(self.__clean)

    def validate_utf8mb4(self, tag):
        """
        Checks the tag does not contain utf8mb4 chars.

        :param tag:
        :return: ``True`` if no utf8mb4 string is found
        """
        if contains_utf8mb4(tag):
            self.errors.append(_(u"Le tag {} contient des caractères utf8mb4").format(tag))
            self.logger.warn("%s contains utf8mb4 char", tag)
            return False
        return True

    @property
    def errors(self):
        return self.__errors
