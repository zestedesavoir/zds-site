from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from zds.api.validators import Validator
from zds.member.models import Profile


class ParticipantsUserValidator(Validator):
    can_be_empty = False

    def validate_participants(self, value):
        msg = None
        if value or self.can_be_empty:
            for participant in value:
                if participant.username == self.get_current_user().username:
                    msg = _("Vous ne pouvez pas vous écrire à vous-même !")
                try:
                    current = get_object_or_404(Profile, user__username=participant)
                    if not Profile.objects.contactable_members().filter(pk=current.pk).exists():
                        msg = _("Vous avez tenté d'ajouter un utilisateur injoignable.")
                except Http404:
                    msg = _(f"Un des participants saisi est introuvable ({participant}).")
        else:
            msg = _("Vous devez spécifier des participants.")
        if msg is not None:
            self.throw_error("participants", msg)
        return value

    def get_current_user(self):
        raise NotImplementedError("`get_current_user()` must be implemented.")


class ParticipantsStringValidator(Validator):
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
            if participants != "":
                if len(participants) == 1 and participants[0].strip() == ",":
                    msg = _("Vous devez spécfier des participants valides.")
                for participant in participants.split(","):
                    participant = participant.strip()
                    if not participant:
                        continue
                    if participant.strip().lower() == username.lower():
                        msg = _("Vous ne pouvez pas vous écrire à vous-même !")
                    try:
                        current = get_object_or_404(Profile, user__username=participant)
                        if not Profile.objects.contactable_members().filter(pk=current.pk).exists():
                            msg = _("Vous avez tenté d'ajouter un utilisateur injoignable.")
                    except Http404:
                        msg = _(f"Un des participants saisi est introuvable ({participant}).")
            else:
                msg = _("Le champ participants ne peut être vide.")
            if msg is not None:
                self.throw_error("participants", msg)
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
            if not value.strip():
                msg = _("Le champ titre ne peut être vide.")
            if msg is not None:
                self.throw_error("title", msg)
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
            if not value.strip():
                msg = _("Le champ text ne peut être vide.")
            if msg is not None:
                self.throw_error("text", msg)
        return value
