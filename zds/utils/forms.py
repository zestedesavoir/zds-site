import logging

from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import Layout, ButtonHolder, Field, Div, HTML
from django.utils.translation import ugettext_lazy as _
from django.template import defaultfilters
from zds.utils.models import Tag
from zds.utils.misc import contains_utf8mb4


class CommonLayoutEditor(Layout):

    def __init__(self, *args, **kwargs):
        super(CommonLayoutEditor, self).__init__(
            Field('text', css_class='md-editor'),
            HTML("<div class='message-bottom'>"),
            HTML("<div class='message-submit'>"),
            StrictButton(
                _('Envoyer'),
                type='submit',
                name='answer'),
            StrictButton(
                _('Aperçu'),
                type='submit',
                name='preview',
                css_class='btn-grey',
                data_ajax_input='preview-message'),
            HTML('</div>'),
            HTML('</div>'),
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
                        _('Envoyer'),
                        type='submit',
                        name='answer'),
                    StrictButton(
                        _('Aperçu'),
                        type='submit',
                        name='preview',
                        css_class='btn-grey preview-btn'),
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
        self.logger = logging.getLogger(__name__)
        self.__clean = []

    def validate_raw_string(self, raw_string):
        """
        validate a string composed as ``tag1,tag2``.

        :param raw_string: the string to be validate. If ``None`` this is considered as a empty str.
        :type raw_string: basestring
        :return: ``True`` if ``raw_string`` is fully valid, ``False`` if at least one error appears. \
        See ``self.errors`` to get all internationalized error.
        """
        if raw_string is None or not isinstance(raw_string, str):
            return self.validate_string_list([])
        return self.validate_string_list(raw_string.split(','))

    def validate_length(self, tag):
        """
        Check the length is in correct range. See ``Tag.label`` max length to have the true upper bound.

        :param tag: the tag lavel to validate
        :return: ``True`` if length is valid
        """
        if len(tag) > Tag._meta.get_field('title').max_length:
            self.errors.append(_('Le tag {} est trop long (maximum {} caractères)'.format(
                tag, Tag._meta.get_field('title').max_length)))
            self.logger.debug('%s est trop long expected=%d got=%d', tag,
                              Tag._meta.get_field('title').max_length, len(tag))
            return False
        return True

    def validate_string_list(self, string_list):
        """
        Same as ``validate_raw_string`` but with a list of tag labels.

        :param string_list:
        :return: ``True`` if ``v`` is fully valid, ``False`` if at least one error appears. See ``self.errors``
        to get all internationalized error.
        """
        string_list = list(filter(lambda s: s.strip(), string_list))  # needed to keep only real candidates
        self.__clean = filter(self.validate_length, string_list)
        self.__clean = filter(self.validate_utf8mb4, self.__clean)
        self.__clean = list(filter(self.validate_no_empty_slug, self.__clean))
        return len(string_list) == len(self.__clean)

    def validate_utf8mb4(self, tag):
        """
        Checks the tag does not contain utf8mb4 chars.

        :param tag:
        :return: ``True`` if no utf8mb4 string is found
        """
        if contains_utf8mb4(tag):
            self.errors.append(_('Le tag {} contient des caractères utf8mb4').format(tag))
            self.logger.warn('%s contains utf8mb4 char', tag)
            return False
        return True

    def validate_no_empty_slug(self, tag):
        """
        Validate whether the tag slug is good

        :param tag:
        :return: ``True`` if the tag slug is good
        """
        if not defaultfilters.slugify(tag):
            self.errors.append(_("Le tag {} n'est constitué que de caractères spéciaux et est donc incorrect"))
            self.logger.warn('%s bad slug', tag)
            return False
        return True

    @property
    def errors(self):
        return self.__errors
