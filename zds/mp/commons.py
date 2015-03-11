# -*- coding: utf-8 -*-

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from zds.member.commons import Validator
from zds.member.models import Profile


class ParticipantsValidator(Validator):
    """
    Validates participants field of a MP.
    """

    def validate_participants(self, value, username):
        """
        Checks about participants.

        :param value: participants value
        :return: participants value
        """
        msg = None
        if value:
            participants = value.strip()
            if participants != '':
                if len(participants) == 1 and participants[0].strip() == ',':
                    msg = _(u'Vous devez spécfier des participants valides')
                for participant in participants.split(','):
                    participant = participant.strip()
                    if participant == '':
                        continue
                    if participant.strip().lower() == username.lower():
                        msg = _(u'Vous ne pouvez pas vous écrire à vous-même !')
                    try:
                        current = get_object_or_404(Profile, user__username=participant)
                        if current.is_private():
                            msg = _(u'Vous avez tenté d\'ajouter un utilisateur injoignable.')
                    except Http404:
                        msg = _(u'Un des participants saisi est introuvable')
            else:
                msg = _(u'Le champ participants ne peut être vide')
            if msg is not None:
                self.throw_error('participants', msg)
        return value


class TitleValidator(Validator):
    """
    Validates title field of a MP.
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
                msg = _(u'Le champ titre ne peut être vide')
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
                msg = _(u'Le champ text ne peut être vide')
            if msg is not None:
                self.throw_error('text', msg)
        return value
