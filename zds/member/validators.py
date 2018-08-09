from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from zds.utils.misc import contains_utf8mb4
from zds.member.models import BannedEmailProvider


def validate_not_empty(value):
    """
    Fields cannot be empty or only contain spaces.

    :param value: value to validate (str or None)
    :return:
    """
    if value is None or not value.strip():
        raise ValidationError(_('Le champs ne peut être vide'))


class ZdSEmailValidator(EmailValidator):
    """
    Based on https://docs.djangoproject.com/en/1.8/_modules/django/core/validators/#EmailValidator
    Changed :
      - check if provider is not if blacklisted
      - check if email is not used by another user
      - remove whitelist check
      - add custom errors and translate them into French
    """
    message = _('Utilisez une adresse de courriel valide.')

    def __call__(self, value, check_username_available=True):
        value = force_text(value)

        if not value or '@' not in value:
            raise ValidationError(self.message, code=self.code)

        user_part, domain_part = value.rsplit('@', 1)

        if not self.user_regex.match(user_part) or contains_utf8mb4(user_part):
            raise ValidationError(self.message, code=self.code)

        # check if provider is blacklisted
        blacklist = BannedEmailProvider.objects.values_list('provider', flat=True)
        for provider in blacklist:
            if '@{}'.format(provider) in value.lower():
                raise ValidationError(_('Ce fournisseur ne peut pas être utilisé.'), code=self.code)

        # check if email is used by another user
        user_count = User.objects.filter(email=value).count()
        if check_username_available and user_count > 0:
            raise ValidationError(_('Cette adresse courriel est déjà utilisée'), code=self.code)
        # check if email exists in database
        elif not check_username_available and user_count == 0:
            raise ValidationError(_('Cette adresse courriel n\'existe pas'), code=self.code)

        if domain_part and not self.validate_domain_part(domain_part):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                if self.validate_domain_part(domain_part):
                    return
            except UnicodeError:
                pass
            raise ValidationError(self.message, code=self.code)


validate_zds_email = ZdSEmailValidator()


def validate_zds_username(value, check_username_available=True):
    """
    Check if username is used by another user

    :param value: value to validate (str or None)
    :return:
    """
    msg = None
    user_count = User.objects.filter(username=value).count()
    if ',' in value:
        msg = _('Le nom d\'utilisateur ne peut contenir de virgules')
    elif value != value.strip():
        msg = _('Le nom d\'utilisateur ne peut commencer ou finir par des espaces')
    elif contains_utf8mb4(value):
        msg = _('Le nom d\'utilisateur ne peut pas contenir des caractères utf8mb4')
    elif check_username_available and user_count > 0:
        msg = _('Ce nom d\'utilisateur est déjà utilisé')
    elif not check_username_available and user_count == 0:
        msg = _('Ce nom d\'utilisateur n\'existe pas')
    if msg is not None:
        raise ValidationError(msg)


def validate_zds_password(value):
    """

    :param value:
    :return:
    """
    if contains_utf8mb4(value):
        raise ValidationError(_('Le mot de passe ne peut pas contenir des caractères utf8mb4'))


def validate_passwords(cleaned_data, password_label='password', password_confirm_label='password_confirm',
                       username=None):
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
        username = cleaned_data.get('username')

    if not password_confirm == password:
        msg = _('Les mots de passe sont différents')

        if password_label in cleaned_data:
            del cleaned_data[password_label]

        if password_confirm_label in cleaned_data:
            del cleaned_data[password_confirm_label]

    if username is not None:
        # Check that password != username
        if password == username:
            msg = _('Le mot de passe doit être différent du pseudo')
            if password_label in cleaned_data:
                del cleaned_data[password_label]
            if password_confirm_label in cleaned_data:
                del cleaned_data[password_confirm_label]

    if msg is not None:
        raise ValidationError(msg)

    return cleaned_data
