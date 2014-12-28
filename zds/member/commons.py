# -*- coding: utf-8 -*-

import os

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from zds.settings import SITE_ROOT


class Updater():

    def result(self, result=None):
        raise NotImplementedError('`result()` must be implemented.')

    def throw_error(self, key=None, message=None):
        raise NotImplementedError('`throw_error()` must be implemented.')


class ProfileUsernameUpdate(Updater):

    def validate_username(self, value):
        """
        Checks about the username.
        """

        msg = None
        if value:
            if value.strip() == '':
                msg = _(u'Le nom d\'utilisateur ne peut-être vide')
            elif User.objects.filter(username=value).count() > 0:
                msg = _(u'Ce nom d\'utilisateur est déjà utilisé')
            # Forbid the use of comma in the username
            elif "," in value:
                msg = _(u'Le nom d\'utilisateur ne peut contenir de virgules')
            elif value != value.strip():
                msg = _(u'Le nom d\'utilisateur ne peut commencer/finir par des espaces')
            if msg is not None:
                self.throw_error("username", msg)
            return self.result(value)
        return self.result()


class ProfileEmailUpdate(Updater):

    def validate_email(self, value):
        """
        Checks about the email.
        """

        if value:
            msg = None
            # Chech if email provider is authorized
            with open(os.path.join(SITE_ROOT, 'forbidden_email_providers.txt'), 'r') as fh:
                for provider in fh:
                    if provider.strip() in value:
                        msg = _(u'Utilisez un autre fournisseur d\'adresses courriel.')
                        break

            # Check that the email is unique
            if User.objects.filter(email=value).count() > 0:
                msg = _(u'Votre adresse courriel est déjà utilisée')
            if msg is not None:
                self.throw_error("email", msg)
            return self.result(value)

        return self.result()