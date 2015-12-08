# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.db import models
from hashlib import md5
from django.http import HttpRequest
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
import os

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.dispatch import receiver

import pygeoip
from zds.forum.models import Post, Topic
from zds.member.managers import ProfileManager
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent
from zds.utils.models import Alert
from importlib import import_module


class Profile(models.Model):
    """
    A user profile. Complementary data of standard Django `auth.user`.
    """

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
        permissions = (
            ("moderation", u"Modérer un membre"),
            ("show_ip", u"Afficher les IP d'un membre"),
        )

    # Link with standard user is a simple one-to-one link, as recommended in official documentation.
    # See https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#extending-the-existing-user-model
    user = models.OneToOneField(
        User,
        verbose_name='Utilisateur',
        related_name="profile")

    last_ip_address = models.CharField(
        'Adresse IP',
        max_length=39,
        blank=True,
        null=True)

    site = models.CharField('Site internet', max_length=2000, blank=True)
    show_email = models.BooleanField('Afficher adresse mail publiquement',
                                     default=False)

    avatar_url = models.CharField(
        'URL de l\'avatar', max_length=2000, null=True, blank=True
    )

    biography = models.TextField('Biographie', blank=True)

    karma = models.IntegerField('Karma', default=0)

    sign = models.TextField('Signature', max_length=500, blank=True)

    show_sign = models.BooleanField('Voir les signatures', default=True)

    # TODO: Change this name. This is a boolean: "true" is "hover" or "click" ?!
    hover_or_click = models.BooleanField('Survol ou click ?', default=False)

    email_for_answer = models.BooleanField('Envoyer pour les réponse MP', default=False)

    # SdZ tutorial IDs separated by columns (:).
    # TODO: bad field name (singular --> should be plural), manually handled multi-valued field.
    sdz_tutorial = models.TextField(
        'Identifiant des tutos SdZ',
        blank=True,
        null=True)

    can_read = models.BooleanField('Possibilité de lire', default=True)
    end_ban_read = models.DateTimeField(
        'Fin d\'interdiction de lecture',
        null=True,
        blank=True)

    can_write = models.BooleanField('Possibilité d\'écrire', default=True)
    end_ban_write = models.DateTimeField(
        'Fin d\'interdiction d\'ecrire',
        null=True,
        blank=True)

    last_visit = models.DateTimeField(
        'Date de dernière visite',
        null=True,
        blank=True)

    objects = ProfileManager()
    _permissions = {}

    def __unicode__(self):
        return self.user.username

    def is_private(self):
        """checks the user can display his stats"""
        user_groups = self.user.groups.all()
        user_group_names = [g.name for g in user_groups]
        return settings.ZDS_APP['member']['bot_group'] in user_group_names

    def get_absolute_url(self):
        """Absolute URL to the profile page."""
        return reverse('member-detail', kwargs={'user_name': self.user.username})

    def get_city(self):
        """
        Uses geo-localization to get physical localization of a profile through its last IP address.
        This works relatively good with IPv4 addresses (~city level), but is very imprecise with IPv6 or exotic internet
        providers.
        :return: The city and the country name of this profile.
        """
        # FIXME: this test to differentiate IPv4 and IPv6 addresses doesn't work, as IPv6 addresses may have length < 16
        # Example: localhost ("::1"). Real test: IPv4 addresses contains dots, IPv6 addresses contains columns.
        if len(self.last_ip_address) <= 16:
            gic = pygeoip.GeoIP(
                os.path.join(
                    settings.GEOIP_PATH,
                    'GeoLiteCity.dat'))
        else:
            gic = pygeoip.GeoIP(
                os.path.join(
                    settings.GEOIP_PATH,
                    'GeoLiteCityv6.dat'))

        geo = gic.record_by_addr(self.last_ip_address)

        if geo is not None:
            return u'{0}, {1}'.format(geo['city'], geo['country_name'])
        return ''

    def get_avatar_url(self):
        """Get the avatar URL for this profile.
        If the user has defined a custom URL, use it.
        If not, use Gravatar.
        :return: The avatar URL for this profile
        :rtype: str
        """
        if self.avatar_url:
            if self.avatar_url.startswith(settings.MEDIA_URL):
                return u"{}{}".format(settings.ZDS_APP["site"]["url"], self.avatar_url)
            else:
                return self.avatar_url
        else:
            return 'https://secure.gravatar.com/avatar/{0}?d=identicon'.format(
                md5(self.user.email.lower().encode("utf-8")).hexdigest())

    def get_post_count(self):
        """
        :return: The forum post count. Doesn't count comments on articles or tutorials.
        """
        return Post.objects.filter(author__pk=self.user.pk, is_visible=True).count()

    def get_post_count_as_staff(self):
        """Number of messages posted (view as staff)."""

        return Post.objects.filter(author__pk=self.user.pk).count()

    def get_topic_count(self):
        """
        :return: the number of topics created by this user.
        """
        return Topic.objects.filter(author=self.user).count()

    def get_user_contents_queryset(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: Queryset of contents with this user as author.
        """
        queryset = PublishableContent.objects.filter(authors__in=[self.user])

        if _type:
            queryset = queryset.filter(type=_type)

        return queryset

    def get_user_public_contents_queryset(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: Queryset of contents with this user as author.
        """
        queryset = PublishedContent.objects.filter(authors__in=[self.user])

        if _type:
            queryset = queryset.filter(content_type=_type)

        return queryset

    def get_content_count(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: the count of contents with this user as author. Count all contents no only published one.
        """
        if self.is_private():
            return 0
        return self.get_user_contents_queryset(_type).count()

    def get_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All contents with this user as author.
        """
        return self.get_user_contents_queryset(_type).all()

    def get_draft_contents(self, _type=None):
        """Return all draft contents with this user as author.
        A draft content is a content which is not published, in validation or in beta.

        :param _type: if provided, request a specific type of content
        :return: All draft tutorials with this user as author.
        """
        return self.get_user_contents_queryset(_type).filter(
            sha_draft__isnull=False,
            sha_beta__isnull=True,
            sha_validation__isnull=True,
            sha_public__isnull=True
        ).all()

    def get_public_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All published contents with this user as author.
        """
        return self.get_user_public_contents_queryset(_type).filter(must_redirect=False).all()

    def get_validate_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All contents in validation with this user as author.
        """
        return self.get_user_contents_queryset(_type).filter(sha_validation__isnull=False).all()

    def get_beta_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All tutorials in beta with this user as author.
        """
        return self.get_user_contents_queryset(_type).filter(sha_beta__isnull=False).all()

    def get_tuto_count(self):
        """
        :return: the count of tutorials with this user as author. Count all tutorials, no only published one.
        """
        return self.get_content_count(_type="TUTORIAL")

    def get_tutos(self):
        """
        :return: All tutorials with this user as author.
        """
        return self.get_contents(_type="TUTORIAL")

    def get_draft_tutos(self):
        """
        Return all draft tutorials with this user as author.
        A draft tutorial is a tutorial which is not published, in validation or in beta.
        :return: All draft tutorials with this user as author.
        """
        return self.get_draft_contents(_type="TUTORIAL")

    def get_public_tutos(self):
        """
        :return: All published tutorials with this user as author.
        """
        return self.get_public_contents(_type="TUTORIAL")

    def get_validate_tutos(self):
        """
        :return: All tutorials in validation with this user as author.
        """
        return self.get_validate_contents(_type="TUTORIAL")

    def get_beta_tutos(self):
        """
        :return: All tutorials in beta with this user as author.
        """
        return self.get_beta_contents(_type="TUTORIAL")

    def get_article_count(self):
        """
        :return: the count of articles with this user as author. Count all articles, no only published one.
        """
        return self.get_content_count(_type="ARTICLE")

    def get_articles(self):
        """
        :return: All articles with this user as author.
        """
        return self.get_contents(_type="ARTICLE")

    def get_public_articles(self):
        """
        :return: All published articles with this user as author.
        """
        return self.get_public_contents(_type="ARTICLE")

    def get_validate_articles(self):
        """
        :return: All articles in validation with this user as author.
        """
        return self.get_validate_contents(_type="ARTICLE")

    def get_draft_articles(self):
        """
        Return all draft article with this user as author.
        A draft article is a article which is not published or in validation.
        :return: All draft article with this user as author.
        """
        return self.get_draft_contents(_type="ARTICLE")

    def get_beta_articles(self):
        """
        :return: All articles in beta with this user as author.
        """
        return self.get_beta_contents(_type="ARTICLE")

    def get_posts(self):
        return Post.objects.filter(author=self.user).all()

    def get_invisible_posts_count(self):
        return Post.objects.filter(is_visible=False, author=self.user).count()

    # TODO: improve this method's name?
    def get_alerts_posts_count(self):
        """
        :return: The number of currently active alerts created by this user.
        """
        return Alert.objects.filter(author=self.user).count()

    def can_read_now(self):
        if self.user.is_authenticated:
            if self.user.is_active:
                if self.end_ban_read:
                    return self.can_read or (
                        self.end_ban_read < datetime.now())
                else:
                    return self.can_read
            else:
                return False

    def can_write_now(self):
        if self.user.is_active:
            if self.end_ban_write:
                return self.can_write or (self.end_ban_write < datetime.now())
            else:
                return self.can_write
        else:
            return False

    def get_followed_topics(self):
        """
        :return: All forum topics followed by this user.
        """
        return Topic.objects.filter(topicfollowed__user=self.user)\
            .order_by('-last_message__pubdate')


@receiver(models.signals.post_delete, sender=User)
def auto_delete_token_on_unregistering(sender, instance, **kwargs):
    """
    This signal receiver deletes forgotten password tokens and registering tokens for the un-registering user;
    """
    TokenForgotPassword.objects.filter(user=instance).delete()
    TokenRegister.objects.filter(user=instance).delete()


class TokenForgotPassword(models.Model):
    """
    When a user forgot its password, the website sends it an email with a token (embedded in a URL).
    If the user has the correct token, it can choose a new password on the dedicated page.
    This model stores the tokens for the users that have forgot their passwords, with an expiration date.
    """
    class Meta:
        verbose_name = 'Token de mot de passe oublié'
        verbose_name_plural = 'Tokens de mots de passe oubliés'

    user = models.ForeignKey(User, verbose_name='Utilisateur', db_index=True)
    token = models.CharField(max_length=100, db_index=True)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        """
        :return: The absolute URL of the "New password" page, including the correct token.
        """
        return reverse('member-new-password') + '?token={0}'.format(self.token)

    def __unicode__(self):
        return u"{0} - {1}".format(self.user.username, self.date_end)


class TokenRegister(models.Model):
    """
    On registration, a token is send by mail to the user. It must use this token (by clicking on a link) to activate its
    account (and prove the email address is correct) and connect itself.
    This model stores the registration token for each user, with an expiration date.
    """
    class Meta:
        verbose_name = 'Token d\'inscription'
        verbose_name_plural = 'Tokens  d\'inscription'

    user = models.ForeignKey(User, verbose_name='Utilisateur', db_index=True)
    token = models.CharField(max_length=100, db_index=True)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        """
        :return: the absolute URL of the account validation page, including the token.
        """
        return reverse('member-active-account') + '?token={0}'.format(self.token)

    def __unicode__(self):
        return u"{0} - {1}".format(self.user.username, self.date_end)


# TODO: Seems unused
def save_profile(backend, user, response, *args, **kwargs):
    profile = Profile.objects.filter(user=user).first()
    if profile is None:
        profile = Profile(user=user,
                          show_email=False,
                          show_sign=True,
                          hover_or_click=True,
                          email_for_answer=False)
        profile.last_ip_address = "0.0.0.0"
        profile.save()


class Ban(models.Model):
    """
    This model stores all sanctions (not only bans).
    It stores sanctioned user, the moderator, the type of sanctions, the reason and the date.
    Note this stores also un-sanctions.
    """

    class Meta:
        verbose_name = 'Sanction'
        verbose_name_plural = 'Sanctions'

    user = models.ForeignKey(User, verbose_name='Sanctionné', db_index=True)
    moderator = models.ForeignKey(User, verbose_name='Moderateur',
                                  related_name='bans', db_index=True)
    type = models.CharField('Type', max_length=80, db_index=True)
    text = models.TextField('Explication de la sanction')
    pubdate = models.DateTimeField(
        'Date de publication',
        blank=True,
        null=True, db_index=True)

    def __unicode__(self):
        return u"{0} - ban : {1} ({2}) ".format(self.user.username, self.text, self.pubdate)


class KarmaNote(models.Model):
    """
    A karma note is a tool for staff to store data about a member.
    Data are:
    - A note (negative values are bad)
    - A comment about the member
    - A date
    This helps the staff to react and stores history of stupidities of a member.
    """
    class Meta:
        verbose_name = 'Note de karma'
        verbose_name_plural = 'Notes de karma'

    user = models.ForeignKey(User, related_name='karmanote_user', db_index=True)
    # TODO: coherence, "staff" is called "moderator" in Ban model.
    staff = models.ForeignKey(User, related_name='karmanote_staff', db_index=True)
    # TODO: coherence, "comment" is called "text" in Ban model.
    comment = models.CharField('Commentaire', max_length=150)
    value = models.IntegerField('Valeur')
    # TODO: coherence, "create_at" is called "pubdate" in Ban model.
    create_at = models.DateTimeField('Date d\'ajout', auto_now_add=True)

    def __unicode__(self):
        return u"{0} - note : {1} ({2}) ".format(self.user.username, self.comment, self.create_at)


def logout_user(username):
    """
    Logout the member.
    :param username: the name of the user to logout.
    """
    now = datetime.now()
    request = HttpRequest()

    sessions = Session.objects.filter(expire_date__gt=now)
    user = User.objects.get(username=username)

    for session in sessions:
        user_id = session.get_decoded().get('_auth_user_id')
        if user.id == user_id:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore(session.session_key)
            logout(request)
            break


def listing():
    """
    Lists all SdZ tutorials stored on the server at `settings.SDZ_TUTO_DIR` location.
    :return: a list of tuples (tutorial ID, path)
    """
    # TODO: French here. Improve the method name.
    fichier = []
    if os.path.isdir(settings.SDZ_TUTO_DIR):
        for root in os.listdir(settings.SDZ_TUTO_DIR):
            if os.path.isdir(os.path.join(settings.SDZ_TUTO_DIR, root)):
                num = root.split('_')[0]
                if num is not None and num.isdigit():
                    fichier.append((num, root))
        return fichier
    else:
        return ()


def get_info_old_tuto(id):
    """
    Retrieve data from SdZ tutorials.
    :param id: The ID of the SdZ tutorial.
    :return: ID, title, tutorial file path, image list file paths, and logo file path of this SdZ tutorial.
    """
    # TODO: French here.
    titre = ''
    tuto = ''
    images = ''
    logo = ''
    if os.path.isdir(settings.SDZ_TUTO_DIR):
        for rep in os.listdir(settings.SDZ_TUTO_DIR):
            if rep.startswith(str(id) + '_'):
                if os.path.isdir(os.path.join(settings.SDZ_TUTO_DIR, rep)):
                    for root, dirs, files in os.walk(
                            os.path.join(
                                settings.SDZ_TUTO_DIR, rep
                            )):
                        for file in files:
                            if file.split('.')[-1] == 'tuto':
                                titre = os.path.splitext(file)[0]
                                tuto = os.path.join(root, file)
                            elif file.split('.')[-1] == 'zip':
                                images = os.path.join(root, file)
                            elif file.split('.')[-1] in ['png',
                                                         'jpg',
                                                         'ico',
                                                         'jpeg',
                                                         'gif']:
                                logo = os.path.join(root, file)

    return id, titre, tuto, images, logo
