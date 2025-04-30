from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, ProhibitNullCharactersValidator
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from zds.member.models import BannedEmailProvider, Profile
from zds.utils.misc import contains_utf8mb4, remove_utf8mb4


def validate_not_empty(value):
    """
    Fields cannot be empty or only contain spaces.

    :param value: value to validate (str or None)
    :return:
    """
    if value is None or not value.strip():
        raise ValidationError(_("Le champs ne peut être vide"))


class ZdSEmailValidator(EmailValidator):
    """
    Based on https://docs.djangoproject.com/en/1.8/_modules/django/core/validators/#EmailValidator
    Changed :
      - check if provider is not if blacklisted
      - check if email is not used by another user
      - remove whitelist check
      - add custom errors and translate them into French
    """

    message = _("Utilisez une adresse de courriel valide.")

    def __call__(self, value, check_username_available=True):
        value = force_str(value)

        if not value or "@" not in value:
            raise ValidationError(self.message, code=self.code)

        user_part, domain_part = value.rsplit("@", 1)

        if not self.user_regex.match(user_part) or contains_utf8mb4(user_part):
            raise ValidationError(self.message, code=self.code)

        # check if provider is blacklisted
        blacklist = BannedEmailProvider.objects.values_list("provider", flat=True)
        for provider in blacklist:
            if f"@{provider}" in value.lower():
                raise ValidationError(_("Ce fournisseur ne peut pas être utilisé."), code=self.code)

        # check if email is used by another user
        user_count = User.objects.filter(email=value).count()
        if check_username_available and user_count > 0:
            raise ValidationError(_("Cette adresse courriel est déjà utilisée"), code=self.code)
        # check if email exists in database
        elif not check_username_available and user_count == 0:
            raise ValidationError(_("Cette adresse courriel n'existe pas"), code=self.code)

        if domain_part and not self.validate_domain_part(domain_part):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode("idna").decode("ascii")
                if self.validate_domain_part(domain_part):
                    return
            except UnicodeError:
                pass
            raise ValidationError(self.message, code=self.code)


validate_zds_email = ZdSEmailValidator()


def clean_username_social_auth(username):
    """
    Clean username of accounts created using social auth.
    """
    # These three conditions are the same as the first three in the "validate_zds_username" function below.
    # If you modify one of them here, make sure you do the same there!
    return remove_utf8mb4(username).replace(",", "").replace("/", "")


def validate_zds_username(value, check_username_available=True):
    """
    Check if username is used by another user

    :param value: value to validate (str or None)
    :return:
    """

    # If the character \x00 is in the username, the homoglyphs library called
    # in Profile.find_username_skeleton() will raise a ValueError (the bug has
    # been reported: https://github.com/yamatt/homoglyphs/issues/6). To prevent
    # this, we call this validator which will raise a ValidationError if \x00 is
    # in the username.
    ProhibitNullCharactersValidator()(value)

    msg = None
    user_count = User.objects.filter(username=value).count()
    skeleton_user_count = Profile.objects.filter(username_skeleton=Profile.find_username_skeleton(value)).count()

    # These first three conditions are the same as those in the "clean_username_social_auth" function above.
    # If you modify one of them here, make sure you do the same there!
    if "," in value:
        msg = _("Le nom d'utilisateur ne peut contenir de virgules")
    elif "/" in value:
        msg = _("Le nom d'utilisateur ne peut contenir de barres obliques")
    elif contains_utf8mb4(value):
        msg = _("Le nom d'utilisateur ne peut pas contenir des caractères utf8mb4")
    elif check_username_available and user_count > 0:
        msg = _("Ce nom d'utilisateur est déjà utilisé")
    elif check_username_available and skeleton_user_count > 0:
        msg = _("Un nom d'utilisateur visuellement proche du votre existe déjà")
    elif not check_username_available and user_count == 0:
        msg = _("Ce nom d'utilisateur n'existe pas")
    if msg is not None:
        raise ValidationError(msg)


def validate_raw_zds_username(data):
    """
    Check if raw username hasn't space on left or right
    """
    msg = None
    username = data.get("username", None)
    if username is None:
        msg = _("Le nom d'utilisateur n'est pas fourni")
    elif username != username.strip():
        msg = _("Le nom d'utilisateur ne peut commencer ou finir par des espaces")

    if msg is not None:
        raise ValidationError(msg)


def validate_zds_password(value):
    """

    :param value:
    :return:
    """
    if contains_utf8mb4(value):
        raise ValidationError(_("Le mot de passe ne peut pas contenir des caractères utf8mb4"))


def validate_passwords(
    cleaned_data, password_label="password", password_confirm_label="password_confirm", username=None
):
    """
    Chek if cleaned_data['password'] == cleaned_data['password_confirm'] and password is not username.
    :param cleaned_data:
    :param password_label:
    :param password_confirm_label:
    :return:
    """

    password = cleaned_data.get(password_label)
    password_confirm = cleaned_data.get(password_confirm_label)
    msg = None

    if username is None:
        username = cleaned_data.get("username")

    if not password_confirm == password:
        msg = _("Les mots de passe sont différents")

        if password_label in cleaned_data:
            del cleaned_data[password_label]

        if password_confirm_label in cleaned_data:
            del cleaned_data[password_confirm_label]

    if username is not None:
        # Check that password != username
        if password == username:
            msg = _("Le mot de passe doit être différent du pseudo")
            if password_label in cleaned_data:
                del cleaned_data[password_label]
            if password_confirm_label in cleaned_data:
                del cleaned_data[password_confirm_label]

    if msg is not None:
        raise ValidationError(msg)

    return cleaned_data
