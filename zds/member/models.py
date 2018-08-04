from datetime import datetime
from hashlib import md5
import os
import pygeoip

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from zds.forum.models import Post, Topic
from zds.member import NEW_PROVIDER_USES
from zds.member.managers import ProfileManager
from zds.tutorialv2.models.database import PublishableContent, PublishedContent
from zds.utils.models import Alert, Licence, Hat

from zds.forum.models import Forum


class Profile(models.Model):
    """
    A user profile. Complementary data of standard Django `auth.user`.
    """

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
        permissions = (
            ('moderation', _('Modérer un membre')),
            ('show_ip', _("Afficher les IP d'un membre")),
        )

    # Link with standard user is a simple one-to-one link, as recommended in official documentation.
    # See https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#extending-the-existing-user-model
    user = models.OneToOneField(
        User,
        verbose_name='Utilisateur',
        related_name='profile')

    last_ip_address = models.CharField(
        'Adresse IP',
        max_length=39,
        blank=True,
        null=True)

    site = models.CharField('Site internet', max_length=2000, blank=True)
    show_email = models.BooleanField('Afficher adresse mail publiquement', default=False)
    avatar_url = models.CharField('URL de l\'avatar', max_length=2000, null=True, blank=True)
    biography = models.TextField('Biographie', blank=True)
    karma = models.IntegerField('Karma', default=0)
    sign = models.TextField('Signature', max_length=500, blank=True)
    licence = models.ForeignKey(Licence,
                                verbose_name='Licence préférée',
                                blank=True, null=True)
    github_token = models.TextField('GitHub', blank=True)
    show_sign = models.BooleanField('Voir les signatures', default=True)
    # do UI components open by hovering them, or is clicking on them required?
    is_hover_enabled = models.BooleanField('Déroulement au survol ?', default=False)
    allow_temp_visual_changes = models.BooleanField('Activer les changements visuels temporaires', default=True)
    show_markdown_help = models.BooleanField("Afficher l'aide Markdown dans l'éditeur", default=True)
    email_for_answer = models.BooleanField('Envoyer pour les réponse MP', default=False)
    hats = models.ManyToManyField(Hat, verbose_name='Casquettes', db_index=True, blank=True)
    can_read = models.BooleanField('Possibilité de lire', default=True)
    end_ban_read = models.DateTimeField("Fin d'interdiction de lecture", null=True, blank=True)
    can_write = models.BooleanField("Possibilité d'écrire", default=True)
    end_ban_write = models.DateTimeField("Fin d'interdiction d'écrire", null=True, blank=True)
    last_visit = models.DateTimeField('Date de dernière visite', null=True, blank=True)
    use_old_smileys = models.BooleanField('Utilise les anciens smileys ?', default=False)
    _permissions = {}
    _groups = None

    objects = ProfileManager()

    def __str__(self):
        return self.user.username

    def is_private(self):
        """Can the user display their stats?"""
        user_groups = self.user.groups.all()
        user_group_names = [g.name for g in user_groups]
        return settings.ZDS_APP['member']['bot_group'] in user_group_names

    def get_absolute_url(self):
        """Absolute URL to the profile page."""
        return reverse('member-detail', kwargs={'user_name': self.user.username})

    def get_city(self):
        """
        Uses geo-localization to get physical localization of a profile through its last IP address.
        This works relatively well with IPv4 addresses (~city level), but is very imprecise with IPv6 or exotic internet
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

        if geo is None:
            return ''

        city = geo['city']
        country = geo['country_name']
        return ', '.join(i for i in [city, country] if i)

    def get_avatar_url(self):
        """Get the avatar URL for this profile.
        If the user has defined a custom URL, use it.
        If not, use Gravatar.
        :return: The avatar URL for this profile
        :rtype: str
        """
        if self.avatar_url:
            if self.avatar_url.startswith(settings.MEDIA_URL):
                return '{}{}'.format(settings.ZDS_APP['site']['url'], self.avatar_url)
            else:
                return self.avatar_url
        else:
            return 'https://secure.gravatar.com/avatar/{0}?d=identicon'.format(
                md5(self.user.email.lower().encode('utf-8')).hexdigest())

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
        return self.get_content_count(_type='TUTORIAL')

    def get_tutos(self):
        """
        :return: All tutorials with this user as author.
        """
        return self.get_contents(_type='TUTORIAL')

    def get_draft_tutos(self):
        """
        Return all draft tutorials with this user as author.
        A draft tutorial is a tutorial which is not published, in validation or in beta.
        :return: All draft tutorials with this user as author.
        """
        return self.get_draft_contents(_type='TUTORIAL')

    def get_public_tutos(self):
        """
        :return: All published tutorials with this user as author.
        """
        return self.get_public_contents(_type='TUTORIAL')

    def get_validate_tutos(self):
        """
        :return: All tutorials in validation with this user as author.
        """
        return self.get_validate_contents(_type='TUTORIAL')

    def get_beta_tutos(self):
        """
        :return: All tutorials in beta with this user as author.
        """
        return self.get_beta_contents(_type='TUTORIAL')

    def get_article_count(self):
        """
        :return: the count of articles with this user as author. Count all articles, no only published one.
        """
        return self.get_content_count(_type='ARTICLE')

    def get_articles(self):
        """
        :return: All articles with this user as author.
        """
        return self.get_contents(_type='ARTICLE')

    def get_public_articles(self):
        """
        :return: All published articles with this user as author.
        """
        return self.get_public_contents(_type='ARTICLE')

    def get_validate_articles(self):
        """
        :return: All articles in validation with this user as author.
        """
        return self.get_validate_contents(_type='ARTICLE')

    def get_draft_articles(self):
        """
        Return all draft article with this user as author.
        A draft article is a article which is not published or in validation.
        :return: All draft article with this user as author.
        """
        return self.get_draft_contents(_type='ARTICLE')

    def get_beta_articles(self):
        """
        :return: All articles in beta with this user as author.
        """
        return self.get_beta_contents(_type='ARTICLE')

    def get_opinion_count(self):
        """
        :return: the count of opinions with this user as author. Count all opinions, no only published one.
        """
        return self.get_content_count(_type='OPINION')

    def get_opinions(self):
        """
        :return: All opinions with this user as author.
        """
        return self.get_contents(_type='OPINION')

    def get_public_opinions(self):
        """
        :return: All published opinions with this user as author.
        """
        return self.get_public_contents(_type='OPINION')

    def get_draft_opinions(self):
        """
        Return all draft opinion with this user as author.
        A draft opinion is a opinion which is not published or in validation.
        :return: All draft opinion with this user as author.
        """
        return self.get_draft_contents(_type='OPINION')

    def get_posts(self):
        return Post.objects.filter(author=self.user).all()

    def get_hidden_by_staff_posts_count(self):
        return Post.objects.filter(is_visible=False, author=self.user).exclude(editor=self.user).count()

    def get_active_alerts_count(self):
        """
        :return: The number of currently active alerts created by this user.
        """
        return Alert.objects.filter(author=self.user, solved=False).count()

    def can_read_now(self):
        if self.user.is_authenticated:
            if self.user.is_active:
                if self.end_ban_read:
                    return self.can_read or (self.end_ban_read < datetime.now())
                return self.can_read
            return False

    def can_write_now(self):
        if self.user.is_active:
            if self.end_ban_write:
                return self.can_write or (self.end_ban_write < datetime.now())
            return self.can_write
        return False

    def get_followed_topics(self):
        """
        :return: All forum topics followed by this user.
        """
        return Topic.objects.filter(topicfollowed__user=self.user)\
            .order_by('-last_message__pubdate')

    def is_dev(self):
        """
        Checks whether user is part of group `settings.ZDS_APP['member']['dev_group']`.
        """
        return self.user.groups.filter(name=settings.ZDS_APP['member']['dev_group']).exists()

    def has_hat(self):
        """
        Checks if this user can at least use one hat.
        """
        return len(self.get_hats()) >= 1

    def get_hats(self):
        """
        Return all hats the user is allowed to use.
        """
        profile_hats = list(self.hats.all())
        groups_hats = list(Hat.objects.filter(group__in=self.user.groups.all()))
        hats = profile_hats + groups_hats
        hats.sort(key=lambda hat: hat.name)
        return hats

    def get_requested_hats(self):
        """
        Return all current hats requested by this user.
        """
        return self.user.requested_hats.filter(is_granted__isnull=True).order_by('-date')

    def get_solved_hat_requests(self):
        """
        Return old hats requested by this user.
        """
        return self.user.requested_hats.filter(is_granted__isnull=False).order_by('-solved_at')

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_write_permission(request):
        return True

    def has_object_write_permission(self, request):
        return self.has_object_update_permission(request) or request.user.has_perm('member.change_profile')

    def has_object_update_permission(self, request):
        return request.user.is_authenticated() and request.user == self.user

    @staticmethod
    def has_ban_permission(request):
        return True

    def has_object_ban_permission(self, request):
        return request.user and request.user.has_perm('member.change_profile')

    @property
    def group_pks(self):
        if self._groups is None:
            self._groups = list(self.user.groups.all())
        return [g.pk for g in self._groups]


@receiver(models.signals.post_delete, sender=User)
def auto_delete_token_on_unregistering(sender, instance, **kwargs):
    """
    This signal receiver deletes forgotten password tokens and registering tokens for the un-registering user;
    """
    TokenForgotPassword.objects.filter(user=instance).delete()
    TokenRegister.objects.filter(user=instance).delete()


@receiver(models.signals.post_save, sender=User)
def remove_token_github_on_removing_from_dev_group(sender, instance, **kwargs):
    """
    This signal receiver removes the GitHub token of a user if he's not in the dev group
    """
    try:
        profile = instance.profile
        if profile.github_token and not profile.is_dev():
            profile.github_token = ''
            profile.save()
    except Profile.DoesNotExist:
        pass


@receiver(models.signals.post_save, sender=Profile)
def remove_hats_linked_to_group(sender, instance, **kwargs):
    """
    When a user is saved, their hats are checked to be sure that none of them is
    linked to a group. In this case, the relevant hat will be removed from the user.
    """
    for hat in instance.hats.all():
        if hat.group:
            instance.hats.remove(hat)


def remove_old_smileys_cookie(response):
    """Remove the Clem smileys cookie by immediate expiration

    :param response: the HTTP response
    :type: django.http.response.HttpResponse
    """

    response.set_cookie(settings.ZDS_APP['member']['old_smileys_cookie_key'], '', expires=0)


def set_old_smileys_cookie(response, profile):
    """Set the Clem smileys cookie according to profile (and if allowed)

    :param response: the HTTP response
    :type: django.http.response.HttpResponse
    :param profile: the profile
    :type profile: Profile
    """

    if settings.ZDS_APP['member']['old_smileys_allowed']:
        if profile.use_old_smileys:
            # TODO: set max_age, expires and so all (see https://stackoverflow.com/a/1623910)
            response.set_cookie(settings.ZDS_APP['member']['old_smileys_cookie_key'], profile.use_old_smileys)
        else:
            remove_old_smileys_cookie(response)


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

    def __str__(self):
        return '{0} - {1}'.format(self.user.username, self.date_end)


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

    def __str__(self):
        return '{0} - {1}'.format(self.user.username, self.date_end)


# Used by SOCIAL_AUTH_PIPELINE to create a profile on first login via social auth
def save_profile(backend, user, response, *args, **kwargs):
    profile = Profile.objects.filter(user=user).first()
    if profile is None:
        profile = Profile(user=user)
        profile.last_ip_address = '0.0.0.0'
        profile.save()


def user_readable_forums(user):
    """Returns a set of forums to which a user can access."""
    return set([f for f in Forum.objects.all() if f.can_read(user)])


class NewEmailProvider(models.Model):
    """A new-used email provider which should be checked by a staff member."""

    class Meta:
        verbose_name = 'Nouveau fournisseur'
        verbose_name_plural = 'Nouveaux fournisseurs'

    provider = models.CharField('Fournisseur', max_length=253, unique=True, db_index=True)
    use = models.CharField('Utilisation', max_length=11, choices=NEW_PROVIDER_USES)
    user = models.ForeignKey(User, verbose_name='Utilisateur concerné', on_delete=models.CASCADE,
                             related_name='new_providers', db_index=True)
    date = models.DateTimeField("Date de l'alerte", auto_now_add=True, db_index=True,
                                db_column='alert_date')

    def __str__(self):
        return 'Alert about the new provider {}'.format(self.provider)


class BannedEmailProvider(models.Model):
    """
    A email provider which has been banned by a staff member.
    It cannot be used for registration.
    """

    class Meta:
        verbose_name = 'Fournisseur banni'
        verbose_name_plural = 'Fournisseurs bannis'

    provider = models.CharField('Fournisseur', max_length=253, unique=True, db_index=True)
    moderator = models.ForeignKey(User, verbose_name='Modérateur', on_delete=models.CASCADE,
                                  related_name='banned_providers', db_index=True)
    date = models.DateTimeField('Date du bannissement', auto_now_add=True, db_index=True,
                                db_column='ban_date')

    def __str__(self):
        return 'Ban of the {} provider'.format(self.provider)


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
    moderator = models.ForeignKey(User, verbose_name='Moderateur', related_name='bans', db_index=True)
    type = models.CharField('Type', max_length=80, db_index=True)
    note = models.TextField('Explication de la sanction')
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True, db_index=True)

    def __str__(self):
        return '{0} - ban : {1} ({2}) '.format(self.user.username, self.note, self.pubdate)


class KarmaNote(models.Model):
    """
    Karma notes are a way of annotating members profiles. They are only visible
    to the staff.

    Fields are:
    - target user and the moderator leaving the note
    - a textual note
    - some amount of karma, negative values being… negative
    """
    class Meta:
        verbose_name = 'Note de karma'
        verbose_name_plural = 'Notes de karma'

    user = models.ForeignKey(User, related_name='karmanote_user', db_index=True)
    moderator = models.ForeignKey(User, related_name='karmanote_staff', db_index=True)
    note = models.CharField('Commentaire', max_length=150)
    karma = models.IntegerField('Valeur')
    pubdate = models.DateTimeField('Date d\'ajout', auto_now_add=True)

    def __str__(self):
        return '{0} - note : {1} ({2}) '.format(self.user.username, self.note, self.pubdate)
