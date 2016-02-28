import os
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from zds.api.validators import Validator
from zds.settings import BASE_DIR


class ProfileUsernameValidator(Validator):
    """
    Validates username field of a profile.
    """

    def validate_username(self, value):
        """
        Checks about the username.

        :param value: username value
        :type value: string
        :return: username value
        :rtype: string
        """
        msg = None
        if value:
            if value.strip() == '':
                msg = _('Le nom d\'utilisateur ne peut-être vide')
            # Forbid the use of comma in the username
            elif "," in value:
                msg = _('Le nom d\'utilisateur ne peut contenir de virgules')
            elif value != value.strip():
                msg = _('Le nom d\'utilisateur ne peut commencer/finir par des espaces')
            elif User.objects.filter(username=value).count() > 0:
                msg = _('Ce nom d\'utilisateur est déjà utilisé')
            if msg is not None:
                self.throw_error('username', msg)
        return value


class ProfileEmailValidator(Validator):
    """
    Validates email field of a profile.
    """

    def validate_email(self, value):
        """
        Checks about the email.

        :param value: email value
        :type value: string
        :return: email value
        :rtype: string
        """
        if value:
            msg = None
            # Chech if email provider is authorized
            with open(os.path.join(BASE_DIR, 'forbidden_email_providers.txt'), 'r') as black_list:
                for provider in black_list:
                    if provider.strip() in value:
                        msg = _('Utilisez un autre fournisseur d\'adresses courriel.')
                        break

            # Check that the email is unique
            if User.objects.filter(email=value).count() > 0:
                msg = _('Votre adresse courriel est déjà utilisée')
            if msg is not None:
                self.throw_error('email', msg)
        return value
