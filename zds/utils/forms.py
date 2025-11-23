import logging

from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import HTML, ButtonHolder, Div, Field, Layout
from django import forms
from django.contrib.auth import authenticate
from django.template import defaultfilters
from django.utils.translation import gettext_lazy as _

from zds.utils.misc import contains_utf8mb4
from zds.utils.models import Tag


class IncludeEasyMDE(Layout):
    """Include EasyMDE JS File for this form"""

    def __init__(self, *args, **kwargs):
        super().__init__(HTML('{% include "easymde.html" %}'), *args, **kwargs)


class CommonLayoutEditor(Layout):
    def __init__(self, *args, **kwargs):
        super().__init__(
            IncludeEasyMDE(),
            Field("text", css_class="md-editor mini-editor"),
            HTML("<div class='message-bottom'>"),
            HTML("<div class='message-submit'>"),
            StrictButton(_("Envoyer"), type="submit", name="answer"),
            StrictButton(
                _("Aperçu"), type="submit", name="preview", css_class="btn-grey", data_ajax_input="preview-message"
            ),
            HTML("</div>"),
            HTML("</div>"),
            *args,
            **kwargs,
        )


class CommonLayoutVersionEditor(Layout):
    def __init__(self, *args, send_label="Envoyer", display_save=False, **kwargs):
        save_button = Div()
        if display_save:
            save_button = StrictButton(
                _("Sauvegarder et continuer"), name="save_and_continue", css_class="btn-grey inline-save-button"
            )
        super().__init__(
            Div(
                IncludeEasyMDE(),
                Field("text", css_class="md-editor"),
                Field("msg_commit"),
                ButtonHolder(
                    StrictButton(_(send_label), type="submit", name="answer"),
                    save_button,
                    StrictButton(_("Aperçu"), type="submit", name="preview", css_class="btn-grey preview-btn"),
                ),
            ),
            *args,
            **kwargs,
        )


class TagValidator:
    """
    validate tags
    """

    error_empty_slug = _("Le tag « {} » n'est constitué que de caractères spéciaux et est donc incorrect.")
    error_tag_too_long = _("Le tag « {} » est trop long (maximum {} caractères).")
    error_utf8mb4 = _("Le tag « {} » contient des caractères utf8mb4.")

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
        return self.validate_string_list(raw_string.split(","))

    def validate_length(self, tag):
        """
        Check the length is in correct range. See ``Tag.label`` max length to have the true upper bound.

        :param tag: the tag lavel to validate
        :return: ``True`` if length is valid
        """
        if len(tag) > Tag._meta.get_field("title").max_length:
            self.errors.append(TagValidator.error_tag_too_long.format(tag, Tag._meta.get_field("title").max_length))
            self.logger.debug(
                "%s est trop long expected=%d got=%d", tag, Tag._meta.get_field("title").max_length, len(tag)
            )
            return False
        return True

    def validate_string_list(self, string_list):
        """
        Same as ``validate_raw_string`` but with a list of tag labels.

        :param string_list:
        :return: ``True`` if ``v`` is fully valid, ``False`` if at least one error appears. \
        See ``self.errors`` to get all internationalized error.
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
            self.errors.append(TagValidator.error_utf8mb4.format(tag))
            self.logger.warning("%s contains utf8mb4 char", tag)
            return False
        return True

    def validate_no_empty_slug(self, tag):
        """
        Validate whether the tag slug is good

        :param tag:
        :return: ``True`` if the tag slug is good
        """
        if not defaultfilters.slugify(tag):
            self.errors.append(TagValidator.error_empty_slug.format(tag))
            self.logger.warning('"%s" bad slug', tag)
            return False
        return True

    @property
    def errors(self):
        return self.__errors


class FieldValidatorMixin:
    def get_non_empty_field_or_error(self, cleaned_data, key, error_message):
        value = cleaned_data.get(key)
        if value is not None and value.strip():
            return value
        else:
            self._errors[key] = self.error_class([error_message()])
            if key in cleaned_data:
                del cleaned_data[key]
            return None

    def check_text_length_limit(self, text, max_length, message_format):
        if len(text) > max_length:
            self._errors["text"] = [message_format().format(max_length)]


class PasswordRequiredForm(forms.Form):
    password = forms.CharField(
        label=_("Mot de passe actuel"),
        widget=forms.PasswordInput,
    )

    def insert_password_required_field(self):
        if self.user.has_usable_password():
            return Field("password")
        else:
            del self.fields["password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")

        if password and self.user and self.user.has_usable_password():
            user_exist = authenticate(username=self.user.username, password=password)
            # Check if the user exist.
            if not user_exist and password != "":
                self._errors["password"] = self.error_class([_("Mot de passe incorrect.")])
                if "password" in cleaned_data:
                    del cleaned_data["password"]
        return cleaned_data
