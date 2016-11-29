# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.defaultfilters import pluralize
from django.utils.translation import ugettext_lazy as _

from zds.member.models import Profile, TokenRegister, Ban
from zds.utils.mps import send_mp


class ProfileCreate(object):
    def create_profile(self, data):
        """
        Creates an inactive profile in the database.

        :param data: Array about an user.
        :type data: array
        :return: instance of a profile inactive
        :rtype: Profile object
        """
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user = User.objects.create_user(username, email, password)
        user.set_password(password)
        user.is_active = False
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        profile = Profile(user=user)
        return profile

    def save_profile(self, profile):
        """
        Saves the profile of a member.

        :param profile: The profile of a member.
        :type data: Profile object
        :return: nothing
        :rtype: None
        """
        profile.save()
        profile.user.save()


class TokenGenerator(object):
    def generate_token(self, user):
        """
        Generates a token for member registration.

        :param user: An User object.
        :type user: User object
        :return: A token object
        :rtype: Token object
        """
        uuid_token = str(uuid.uuid4())
        date_end = datetime.now() + timedelta(hours=1)
        token = TokenRegister(user=user, token=uuid_token, date_end=date_end)
        token.save()
        return token

    def send_email(self, token, user):
        """
        Sends an email with a confirmation a registration which contain a link for registration validation.

        :param token: The token for registration validation.
        :type token: Token Object
        :param user: The user just registered.
        :type user: User object
        :return: nothing
        :rtype: None
        """
        subject = _(u'{} - Confirmation d\'inscription').format(settings.ZDS_APP['site']['litteral_name'])
        from_email = u'{} <{}>'.format(settings.ZDS_APP['site']['litteral_name'],
                                       settings.ZDS_APP['site']['email_noreply'])
        context = {
            'username': user.username,
            'url': settings.ZDS_APP['site']['url'] + token.get_absolute_url(),
            'site_name': settings.ZDS_APP['site']['litteral_name'],
            'site_url': settings.ZDS_APP['site']['url']
        }
        message_html = render_to_string('email/member/confirm_registration.html', context)
        message_txt = render_to_string('email/member/confirm_registration.txt', context)

        msg = EmailMultiAlternatives(subject, message_txt, from_email, [user.email])
        msg.attach_alternative(message_html, 'text/html')
        try:
            msg.send()
        except Exception:
            pass


class MemberSanctionState(object):
    """
    Super class of the enumeration to know which sanction it is.
    """

    array_infos = None

    def __init__(self, array_infos):
        super(MemberSanctionState, self).__init__()
        self.array_infos = array_infos

    def get_type(self):
        """
        Gets the type of a sanction.

        :return: type of the sanction.
        :rtype: ugettext_lazy
        """
        raise NotImplementedError('`get_type()` must be implemented.')

    def get_text(self):
        """
        Gets the text of a sanction.

        :return: text of the sanction.
        :rtype: string
        """
        raise NotImplementedError('`get_text()` must be implemented.')

    def get_detail(self):
        """
        Gets detail of a sanction.

        :return: detail of the sanction.
        :rtype: ugettext_lazy
        """
        raise NotImplementedError('`get_detail()` must be implemented.')

    def apply_sanction(self, profile, ban):
        """
        Applies the sanction with the `ban` object on a member with the `profile` object
        and saves these objects.

        :param profile: Member concerned by the sanction.
        :type profile: Profile object
        :param ban: Sanction.
        :type ban: Ban object
        :return: nothing
        :rtype: None
        """
        raise NotImplementedError('`apply_sanction()` must be implemented.')

    def get_sanction(self, moderator, user):
        """
        Gets the sanction according to the type of the sanction.

        :param moderator: Moderator who applies the sanction.
        :type moderator: User object
        :param user: User sanctioned.
        :type user: User object
        :return: sanction
        :rtype: Ban object
        """
        ban = Ban()
        ban.moderator = moderator
        ban.user = user
        ban.pubdate = datetime.now()
        ban.type = self.get_type()
        ban.note = self.get_text()
        return ban

    def get_message_unsanction(self):
        """
        Gets the message for an un-sanction.

        :return: message of the un-sanction.
        :rtype: ugettext_lazy
        """
        return _(u'Bonjour **{0}**,\n\n'
                 u'**Bonne nouvelle**, la sanction qui '
                 u'pesait sur vous a été levée par **{1}**.\n\n'
                 u'Ce qui signifie que {3}\n\n'
                 u'Le motif est :\n\n'
                 u'> {4}\n\n'
                 u'Cordialement, \n\n L\'équipe {5}.')

    def get_message_sanction(self):
        """
        Gets the message for a sanction.

        :return: message of the sanction.
        :rtype: ugettext_lazy
        """
        return _(u'Bonjour **{0}**,\n\n'
                 u'Vous avez été santionné par **{1}**.\n\n'
                 u'La sanction est de type *{2}*, ce qui signifie que {3}\n\n'
                 u'Le motif de votre sanction est :\n\n'
                 u'> {4}\n\n'
                 u'Cordialement, \n\nL\'équipe {5}.')

    def notify_member(self, ban, msg):
        """
        Notify the member sanctioned with a MP.

        :param ban: Sanction.
        :type ban: Ban object
        :param msg: message send at the user sanctioned.
        :type msg: string object
        :return: nothing
        :rtype: None
        """
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            [ban.user],
            ban.type,
            "",
            msg,
            True,
            direct=True,
        )


class ReadingOnlySanction(MemberSanctionState):
    """
    State of the sanction reading only.
    """

    def get_type(self):
        return _(u"Lecture Seule")

    def get_text(self):
        return self.array_infos.get('ls-text', '')

    def get_detail(self):
        return (_(u'vous ne pouvez plus poster dans les forums, ni dans les '
                  u'commentaires d\'articles et de tutoriels.'))

    def apply_sanction(self, profile, ban):
        profile.end_ban_write = None
        profile.can_write = False
        profile.save()
        ban.save()


class TemporaryReadingOnlySanction(MemberSanctionState):
    """
    State of the sanction reading only temporary.
    """

    def get_type(self):
        return _(u"Lecture Seule Temporaire")

    def get_text(self):
        return self.array_infos.get('ls-text', '')

    def get_detail(self):
        jrs = int(self.array_infos.get("ls-jrs"))
        return (_(u'vous ne pouvez plus poster dans les forums, ni dans les '
                  u'commentaires d\'articles et de tutoriels pendant {0} jour{1}.')
                .format(jrs, pluralize(jrs)))

    def apply_sanction(self, profile, ban):
        day = int(self.array_infos.get("ls-jrs"))
        profile.end_ban_write = datetime.now() + timedelta(days=day, hours=0, minutes=0, seconds=0)
        profile.can_write = False
        profile.save()
        ban.save()


class DeleteReadingOnlySanction(MemberSanctionState):
    """
    State of the un-sanction reading only.
    """

    def get_type(self):
        return _(u"Autorisation d'écrire")

    def get_text(self):
        return self.array_infos.get('unls-text', '')

    def get_detail(self):
        return (_(u'vous pouvez désormais poster sur les forums, dans les '
                  u'commentaires d\'articles et tutoriels.'))

    def apply_sanction(self, profile, ban):
        profile.can_write = True
        profile.end_ban_write = None
        profile.save()
        ban.save()


class BanSanction(MemberSanctionState):
    """
    State of the sanction ban.
    """

    def get_type(self):
        return _(u"Ban définitif")

    def get_text(self):
        return self.array_infos.get('ban-text', '')

    def get_detail(self):
        return _(u"vous ne pouvez plus vous connecter sur {0}.") \
            .format(settings.ZDS_APP['site']['litteral_name'])

    def apply_sanction(self, profile, ban):
        profile.end_ban_read = None
        profile.can_read = False
        profile.save()
        ban.save()


class TemporaryBanSanction(MemberSanctionState):
    """
    State of the sanction ban temporary.
    """

    def get_type(self):
        return _(u"Ban Temporaire")

    def get_text(self):
        return self.array_infos.get('ban-text', '')

    def get_detail(self):
        jrs = int(self.array_infos.get("ban-jrs"))
        return (_(u'vous ne pouvez plus vous connecter sur {0} pendant {1} jour{2}.')
                .format(settings.ZDS_APP['site']['litteral_name'],
                        jrs,
                        pluralize(jrs)))

    def apply_sanction(self, profile, ban):
        day = int(self.array_infos.get("ban-jrs"))
        profile.end_ban_read = datetime.now() + timedelta(days=day, hours=0, minutes=0, seconds=0)
        profile.can_read = False
        profile.save()
        ban.save()


class DeleteBanSanction(MemberSanctionState):
    """
    State of the un-sanction ban.
    """

    def get_type(self):
        return _(u"Autorisation de se connecter")

    def get_text(self):
        return self.array_infos.get('unban-text', '')

    def get_detail(self):
        return _(u"vous pouvez désormais vous connecter sur le site.")

    def apply_sanction(self, profile, ban):
        profile.can_read = True
        profile.end_ban_read = None
        profile.save()
        ban.save()
