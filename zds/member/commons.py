# -*- coding: utf-8 -*-

import os
import uuid

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from zds.member.models import Profile, TokenRegister
from zds.settings import SITE_ROOT


class Validator():

    def result(self, result=None):
        raise NotImplementedError('`result()` must be implemented.')

    def throw_error(self, key=None, message=None):
        raise NotImplementedError('`throw_error()` must be implemented.')


class ProfileUsernameValidator(Validator):

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


class ProfileEmailValidator(Validator):

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


class ProfileCreate():

    def create_profile(self, data):
        user = User.objects.create_user(data.get("username"),
                                        data.get("email"),
                                        data.get("password"))
        user.set_password(data.get("password"))
        user.is_active = False
        user.backend = "django.contrib.auth.backends.ModelBackend"
        profile = Profile(user=user,
                          show_email=False,
                          show_sign=True,
                          hover_or_click=True,
                          email_for_answer=False)
        return profile

    def save_profile(self, profile):
        profile.save()
        profile.user.save()

    def generate_token(self, user):
        uuid_token = str(uuid.uuid4())
        date_end = datetime.now() + timedelta(days=0,
                                              hours=1,
                                              minutes=0,
                                              seconds=0)
        token = TokenRegister(user=user,
                              token=uuid_token,
                              date_end=date_end)
        token.save()
        return token

    def send_email(self, token, user):
        subject = _(u"{} - Confirmation d'inscription").format(settings.ZDS_APP['site']['abbr'])
        from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                      settings.ZDS_APP['site']['email_noreply'])
        message_html = get_template("email/register/confirm.html").render(Context(
            {"username": user.username,
             "url": settings.ZDS_APP['site']['url'] + token.get_absolute_url(),
             "site_name": settings.ZDS_APP['site']['name'],
             "site_url": settings.ZDS_APP['site']['url']}))
        message_txt = get_template("email/register/confirm.txt") .render(Context(
            {"username": user.username,
             "url": settings.ZDS_APP['site']['url'] + token.get_absolute_url(),
             "site_name": settings.ZDS_APP['site']['name'],
             "site_url": settings.ZDS_APP['site']['url']}))
        msg = EmailMultiAlternatives(subject, message_txt, from_email, [user.email])
        msg.attach_alternative(message_html, "text/html")
        try:
            msg.send()
        except:
            pass
