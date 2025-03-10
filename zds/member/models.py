import logging
from datetime import datetime
from hashlib import md5

import homoglyphs as hg
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Forum, Post, Topic
from zds.member import NEW_PROVIDER_USES
from zds.member.managers import ProfileManager
from zds.member.utils import get_geo_location_from_ip
from zds.notification.models import TopicAnswerSubscription
from zds.tutorialv2.models.database import PublishableContent
from zds.utils import old_slugify
from zds.utils.models import Alert, Hat, Licence


class Profile(models.Model):
    """
    A user profile. Complementary data of standard Django `auth.user`.
    """

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
        permissions = (
            ("moderation", _("Modérer un membre")),
            ("show_ip", _("Afficher les IP d'un membre")),
        )

    # Link with standard user is a simple one-to-one link, as recommended in official documentation.
    # See https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#extending-the-existing-user-model
    user = models.OneToOneField(User, verbose_name="Utilisateur", related_name="profile", on_delete=models.CASCADE)
    username_skeleton = models.CharField("Squelette du username", max_length=150, null=True, blank=True, db_index=True)

    last_ip_address = models.CharField("Adresse IP", max_length=39, blank=True, null=True)

    site = models.CharField("Site internet", max_length=2000, blank=True)
    show_email = models.BooleanField("Afficher adresse mail publiquement", default=False)
    avatar_url = models.CharField("URL de l'avatar", max_length=2000, null=True, blank=True)
    biography = models.TextField("Biographie", blank=True)
    karma = models.IntegerField("Karma", default=0)
    sign = models.TextField("Signature", max_length=500, blank=True)
    licence = models.ForeignKey(
        Licence, verbose_name="Licence préférée", blank=True, null=True, on_delete=models.SET_NULL
    )
    github_token = models.TextField("GitHub", blank=True)
    show_sign = models.BooleanField("Voir les signatures", default=True)
    hide_forum_activity = models.BooleanField(
        "Masquer l'activité de forum et les commentaires sur la page de profil", default=False
    )
    # do UI components open by hovering them, or is clicking on them required?
    is_hover_enabled = models.BooleanField("Déroulement au survol ?", default=False)
    allow_temp_visual_changes = models.BooleanField("Activer les changements visuels temporaires", default=True)
    show_markdown_help = models.BooleanField("Afficher l'aide Markdown dans l'éditeur", default=True)
    email_for_answer = models.BooleanField("Envoyer pour les réponse MP", default=False)
    email_for_new_mp = models.BooleanField("Envoyer pour les nouveaux MP", default=False)
    hats = models.ManyToManyField(Hat, verbose_name="Casquettes", db_index=True, blank=True)
    can_read = models.BooleanField("Possibilité de lire", default=True)
    end_ban_read = models.DateTimeField("Fin d'interdiction de lecture", null=True, blank=True)
    can_write = models.BooleanField("Possibilité d'écrire", default=True)
    end_ban_write = models.DateTimeField("Fin d'interdiction d'écrire", null=True, blank=True)
    last_visit = models.DateTimeField("Date de dernière visite", null=True, blank=True)
    _permissions = {}
    _groups = None
    _hats = None
    _cached_city = None

    objects = ProfileManager()

    def __str__(self):
        return self.user.username

    def is_private(self):
        """Can the user display their stats?"""
        user_groups = self.user.groups.all()
        user_group_names = [g.name for g in user_groups]
        return settings.ZDS_APP["member"]["bot_group"] in user_group_names

    def get_absolute_url(self):
        """Absolute URL to the profile page."""
        return reverse("member-detail", kwargs={"user_name": self.user.username})

    def get_city(self):
        """
        Uses geo-localization to get physical localization of a profile through
        its last IP address. This works relatively well with IPv4 addresses (~city level),
        but is very imprecise with IPv6 or exotic internet providers.
        The result is cached on an instance level because this method is called
        a lot in the profile.
        :return: The city and the country name of this profile.
        """
        if self._cached_city is not None and self._cached_city[0] == self.last_ip_address:
            return self._cached_city[1]

        geo_location = get_geo_location_from_ip(self.last_ip_address)

        self._cached_city = (self.last_ip_address, geo_location)

        return geo_location

    def get_absolute_avatar_url(self):
        """Gets the avatar URL of this profile.
        :return: The absolute URL of this profile's avatar
        :rtype: str or None
        """
        if self.avatar_url and self.avatar_url.startswith(settings.MEDIA_URL):
            return settings.ZDS_APP["site"]["url"] + self.avatar_url
        return self.avatar_url

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
        :return: Queryset of public contents with this user as author.
        """
        queryset = PublishableContent.objects.filter(public_version__authors__in=[self.user])

        if _type:
            queryset = queryset.filter(type=_type)

        return queryset

    def get_user_draft_contents_queryset(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: Queryset of draft contents with this user as author.
        """
        return self.get_user_contents_queryset(_type).filter(
            sha_draft__isnull=False, sha_beta__isnull=True, sha_validation__isnull=True, sha_public__isnull=True
        )

    def get_user_validate_contents_queryset(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: Queryset of contents in validation with this user as author.
        """
        return self.get_user_contents_queryset(_type).filter(sha_validation__isnull=False)

    def get_user_beta_contents_queryset(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: Queryset of contents in beta with this user as author.
        """
        return self.get_user_contents_queryset(_type).filter(sha_beta__isnull=False)

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
        return self.get_user_draft_contents_queryset(_type).all()

    def get_public_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All published contents with this user as author.
        """
        return self.get_user_public_contents_queryset(_type).all()

    def get_validate_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All contents in validation with this user as author.
        """
        return self.get_user_validate_contents_queryset(_type).all()

    def get_beta_contents(self, _type=None):
        """
        :param _type: if provided, request a specific type of content
        :return: All tutorials in beta with this user as author.
        """
        return self.get_user_beta_contents_queryset(_type).all()

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

    def get_opinions(self):
        """
        :return: All opinions with this user as author.
        """
        return self.get_contents(_type="OPINION")

    def get_public_opinions(self):
        """
        :return: All published opinions with this user as author.
        """
        return self.get_public_contents(_type="OPINION")

    def get_draft_opinions(self):
        """
        Return all draft opinion with this user as author.
        A draft opinion is a opinion which is not published or in validation.
        :return: All draft opinion with this user as author.
        """
        return self.get_draft_contents(_type="OPINION")

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

    def is_banned(self):
        """Return True if the user is permanently or temporarily banned."""
        if self.end_ban_read:
            return not self.can_read and (self.end_ban_read >= datetime.now())
        return not self.can_read

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
        return TopicAnswerSubscription.objects.get_objects_followed_by(self.user.id)

    def get_followed_topic_count(self):
        """
        :return: the number of topics followeded by this user.
        """
        return TopicAnswerSubscription.objects.get_objects_followed_by(self.user.id).count()

    def is_dev(self):
        """
        Checks whether user is part of group `settings.ZDS_APP['member']['dev_group']`.
        """
        return self.user.groups.filter(name=settings.ZDS_APP["member"]["dev_group"]).exists()

    def has_hat(self):
        """
        Checks if this user can at least use one hat.
        """
        return len(self.get_hats()) >= 1

    def get_hats(self):
        """
        Return all hats the user is allowed to use.
        """
        if self._hats is None:
            profile_hats = list(self.hats.all())
            groups_hats = list(Hat.objects.filter(group__in=self.user.groups.all()))
            self._hats = profile_hats + groups_hats

            # We sort internal hats before the others, and we slugify for sorting to sort correctly
            # with diatrics.
            self._hats.sort(key=lambda hat: f'{"a" if hat.is_staff else "b"}-{old_slugify(hat.name)}')

        return self._hats

    def get_requested_hats(self):
        """
        Return all current hats requested by this user.
        """
        return self.user.requested_hats.filter(is_granted__isnull=True).order_by("-date")

    def get_solved_hat_requests(self):
        """
        Return old hats requested by this user.
        """
        return self.user.requested_hats.filter(is_granted__isnull=False).order_by("-solved_at")

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_write_permission(request):
        return True

    def has_object_write_permission(self, request):
        return self.has_object_update_permission(request) or request.user.has_perm("member.change_profile")

    def has_object_update_permission(self, request):
        return request.user.is_authenticated and request.user == self.user

    @staticmethod
    def has_ban_permission(request):
        return True

    def has_object_ban_permission(self, request):
        return request.user and request.user.has_perm("member.change_profile")

    @property
    def group_pks(self):
        if self._groups is None:
            self._groups = list(self.user.groups.all())
        return [g.pk for g in self._groups]

    @staticmethod
    def find_username_skeleton(username):
        skeleton = ""
        for ch in username:
            homoglyph = hg.Homoglyphs(languages={"fr"}, strategy=hg.STRATEGY_LOAD).to_ascii(ch)
            if len(homoglyph) > 0 and homoglyph[0].strip() != "":
                skeleton += homoglyph[0]
        return skeleton.lower()


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
            profile.github_token = ""
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


class TokenForgotPassword(models.Model):
    """
    When a user forgot its password, the website sends it an email with a token (embedded in a URL).
    If the user has the correct token, it can choose a new password on the dedicated page.
    This model stores the tokens for the users that have forgot their passwords, with an expiration date.
    """

    class Meta:
        verbose_name = "Token de mot de passe oublié"
        verbose_name_plural = "Tokens de mots de passe oubliés"

    user = models.ForeignKey(User, verbose_name="Utilisateur", db_index=True, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, db_index=True)
    date_end = models.DateTimeField("Date de fin")

    def get_absolute_url(self):
        """
        :return: The absolute URL of the "New password" page, including the correct token.
        """
        return reverse("member-new-password") + f"?token={self.token}"

    def __str__(self):
        return f"{self.user.username} - {self.date_end}"


class TokenRegister(models.Model):
    """
    On registration, a token is send by mail to the user. It must use this token (by clicking on a link) to activate its
    account (and prove the email address is correct) and connect itself.
    This model stores the registration token for each user, with an expiration date.
    """

    class Meta:
        verbose_name = "Token d'inscription"
        verbose_name_plural = "Tokens  d'inscription"

    user = models.ForeignKey(User, verbose_name="Utilisateur", db_index=True, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, db_index=True)
    date_end = models.DateTimeField("Date de fin")

    def get_absolute_url(self):
        """
        :return: the absolute URL of the account validation page, including the token.
        """
        return reverse("member-active-account") + f"?token={self.token}"

    def __str__(self):
        return f"{self.user.username} - {self.date_end}"


# Used by SOCIAL_AUTH_PIPELINE to create a profile on first login via social auth
def save_profile(backend, user, response, *args, **kwargs):
    profile = Profile.objects.filter(user=user).first()
    if profile is None:
        profile = Profile(user=user)
        profile.last_ip_address = "0.0.0.0"
        profile.save()


def user_readable_forums(user):
    """Returns a set of forums to which a user can access."""
    return {f for f in Forum.objects.all() if f.can_read(user)}


class NewEmailProvider(models.Model):
    """A new-used email provider which should be checked by a staff member."""

    class Meta:
        verbose_name = "Nouveau fournisseur"
        verbose_name_plural = "Nouveaux fournisseurs"

    provider = models.CharField("Fournisseur", max_length=253, unique=True, db_index=True)
    use = models.CharField("Utilisation", max_length=11, choices=NEW_PROVIDER_USES)
    user = models.ForeignKey(
        User, verbose_name="Utilisateur concerné", on_delete=models.CASCADE, related_name="new_providers", db_index=True
    )
    date = models.DateTimeField("Date de l'alerte", auto_now_add=True, db_index=True, db_column="alert_date")

    def __str__(self):
        return f"Alert about the new provider {self.provider}"


class BannedEmailProvider(models.Model):
    """
    A email provider which has been banned by a staff member.
    It cannot be used for registration.
    """

    class Meta:
        verbose_name = "Fournisseur banni"
        verbose_name_plural = "Fournisseurs bannis"

    provider = models.CharField("Fournisseur", max_length=253, unique=True, db_index=True)
    moderator = models.ForeignKey(
        User, verbose_name="Modérateur", on_delete=models.CASCADE, related_name="banned_providers", db_index=True
    )
    date = models.DateTimeField("Date du bannissement", auto_now_add=True, db_index=True, db_column="ban_date")

    def __str__(self):
        return f"Ban of the {self.provider} provider"


class Ban(models.Model):
    """
    This model stores all sanctions (not only bans).
    It stores sanctioned user, the moderator, the type of sanctions, the reason and the date.
    Note this stores also un-sanctions.
    """

    class Meta:
        verbose_name = "Sanction"
        verbose_name_plural = "Sanctions"

    user = models.ForeignKey(User, verbose_name="Sanctionné", db_index=True, on_delete=models.CASCADE)
    moderator = models.ForeignKey(
        User, verbose_name="Moderateur", related_name="bans", db_index=True, on_delete=models.SET_NULL, null=True
    )  # use default user?
    type = models.CharField("Type", max_length=80, db_index=True)
    note = models.TextField("Explication de la sanction")
    pubdate = models.DateTimeField("Date de publication", blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} - ban : {self.note} ({self.pubdate}) "


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
        verbose_name = "Note de karma"
        verbose_name_plural = "Notes de karma"

    user = models.ForeignKey(User, related_name="karmanote_user", db_index=True, on_delete=models.CASCADE)
    moderator = models.ForeignKey(
        User, related_name="karmanote_staff", db_index=True, on_delete=models.SET_NULL, null=True
    )
    note = models.TextField("Commentaire")
    karma = models.IntegerField("Valeur")
    pubdate = models.DateTimeField("Date d'ajout", auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - note : {self.note} ({self.pubdate}) "
