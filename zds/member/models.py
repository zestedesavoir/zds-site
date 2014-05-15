# coding: utf-8

from datetime import datetime
from hashlib import md5
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

import pygeoip
from zds.article.models import Article
from zds.forum.models import Post, Topic
from zds.tutorial.models import Tutorial
from zds.utils.models import Alert


class Profile(models.Model):

    """Represents an user profile."""
    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
        permissions = (
            ("moderation", u"Modérer un membre"),
            ("show_ip", u"Afficher les IP d'un membre"),
        )

    user = models.OneToOneField(User, verbose_name='Utilisateur', related_name="profile")

    last_ip_address = models.CharField(
        'Adresse IP',
        max_length=15,
        blank=True,
        null=True)

    site = models.CharField('Site internet', max_length=128, blank=True)
    show_email = models.BooleanField('Afficher adresse mail publiquement',
                                     default=False)

    avatar_url = models.CharField(
        'URL de l\'avatar', max_length=128, null=True, blank=True
    )

    biography = models.TextField('Biographie', blank=True)

    karma = models.IntegerField('Karma', default=0)

    sign = models.TextField('Signature', max_length=250, blank=True)

    show_sign = models.BooleanField('Voir les signatures',
                                    default=True)

    hover_or_click = models.BooleanField('Survol ou click ?',
                                         default=False)

    email_for_answer = models.BooleanField('Envoyer pour les réponse MP',
                                         default=False)

    sdz_tutorial = models.CharField('Identifiant des tutos SdZ', max_length=30, blank=True, null=True)

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

    def __unicode__(self):
        """Textual forum of a profile."""
        return self.user.username

    def get_absolute_url(self):
        """Absolute URL to the profile page."""
        return reverse('zds.member.views.details',
                       kwargs={'user_name': self.user.username })

    def get_city(self):
        """return physical adress by geolocalisation."""
        gic = pygeoip.GeoIP(
            os.path.join(
                settings.GEOIP_PATH,
                'GeoLiteCity.dat'))
        geo = gic.record_by_addr(self.last_ip_address)

        return u'{0} ({1}) : {2}'.format(
            geo['city'], geo['postal_code'], geo['country_name'])

    def get_avatar_url(self):
        """Avatar URL (using custom URL or Gravatar)"""
        if self.avatar_url:
            return self.avatar_url
        else:
            return 'https://secure.gravatar.com/avatar/{0}?d=identicon'.format(
                md5(self.user.email).hexdigest())

    def get_post_count(self):
        """Number of messages posted."""
        return Post.objects.filter(author__pk=self.user.pk).count()

    def get_topic_count(self):
        """Number of threads created."""
        return Topic.objects.filter(author=self.user).count()

    def get_tuto_count(self):
        """Number of tutos created."""
        return Tutorial.objects.filter(authors__in=[self.user]).count()

    def get_tutos(self):
        """Get all tutorials of the user."""
        return Tutorial.objects.filter(authors__in=[self.user]).all()

    def get_draft_tutos(self):
        """Tutorial in draft."""
        return Tutorial.objects.filter(
            authors__in=[
                self.user],
            sha_draft__isnull=False).all()

    def get_public_tutos(self):
        """Tutorial in public."""
        return Tutorial.objects.filter(
            authors__in=[
                self.user],
            sha_public__isnull=False).all()

    def get_validate_tutos(self):
        """Tutorial in validation."""
        return Tutorial.objects.filter(
            authors__in=[
                self.user],
            sha_validation__isnull=False).all()

    def get_beta_tutos(self):
        """Tutorial in beta."""
        return Tutorial.objects.filter(
            authors__in=[
                self.user],
            sha_beta__isnull=False).all()

    def get_articles(self):
        """Get all articles of the user."""
        return Article.objects.filter(authors__in=[self.user]).all()

    def get_public_articles(self):
        """Get all public articles of the user."""
        return Article.objects.filter(
            authors__in=[
                self.user],
            sha_public__isnull=False).all()

    def get_validate_articles(self):
        """Articles in validation."""
        return Article.objects.filter(
            authors__in=[
                self.user],
            sha_validation__isnull=False).all()

    def get_draft_articles(self):
        """Get all draft articles of the user."""
        return Article.objects.filter(
            authors__in=[
                self.user],
            sha_draft__isnull=False).all()

    def get_posts(self):
        return Post.objects.filter(author=self.user).all()

    def get_invisible_posts_count(self):
        return Post.objects.filter(is_visible=False, author=self.user).count()

    def get_alerts_posts_count(self):
        return Alert.objects.filter(author=self.user).count()

    def can_read_now(self):
        if self.user.is_authenticated:
            if self.user.is_active:
                if self.end_ban_read:
                    return self.can_read or (self.end_ban_read < datetime.now())
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
        """Followed topics."""
        return Topic.objects.filter(topicfollowed__user=self.user)\
            .order_by('-last_message__pubdate')


class TokenForgotPassword(models.Model):

    class Meta:
        verbose_name = 'Token de mot de passe oublié'
        verbose_name_plural = 'Tokens de mots de passe oubliés'

    user = models.ForeignKey(User, verbose_name='Utilisateur')
    token = models.CharField(max_length=100)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        """Absolute URL to the new password page."""
        return reverse('zds.member.views.new_password') + \
            '?token={0}'.format(self.token)


class TokenRegister(models.Model):

    class Meta:
        verbose_name = 'Token d\'inscription'
        verbose_name_plural = 'Tokens  d\'inscription'

    user = models.ForeignKey(User, verbose_name='Utilisateur')
    token = models.CharField(max_length=100)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        """Absolute URL to the active account page."""
        return reverse('zds.member.views.active_account') + \
            '?token={0}'.format(self.token)

    def __unicode__(self):
        """Textual forum of a profile."""
        return u"{0} - {1}".format(self.user.username, self.date_end)


class Ban(models.Model):

    class Meta:
        verbose_name = 'Sanction'
        verbose_name_plural = 'Sanctions'

    user = models.ForeignKey(User, verbose_name='Sanctionné')
    moderator = models.ForeignKey(User, verbose_name='Moderateur',
                                  related_name='bans')
    type = models.CharField('Type', max_length=80)
    text = models.TextField('Explication de la sanction')
    pubdate = models.DateTimeField(
        'Date de publication',
        blank=True,
        null=True)

def listing():

    fichier = []
    if os.path.isdir(settings.SDZ_TUTO_DIR):
        for root in os.listdir(settings.SDZ_TUTO_DIR):
            if os.path.isdir(os.path.join(settings.SDZ_TUTO_DIR, root)):
                num = root.split('_')[0]
                if num != None and num.isdigit():
                    fichier.append((num, root))
        return fichier
    else:
        return ()

def get_info_old_tuto(id):
    titre = ''
    tuto = ''
    images = ''
    logo = ''
    if os.path.isdir(settings.SDZ_TUTO_DIR):
        for rep in os.listdir(settings.SDZ_TUTO_DIR):
            if rep.startswith(str(id)+'_'):
                if os.path.isdir(os.path.join(settings.SDZ_TUTO_DIR, rep)):
                    for root, dirs, files in os.walk(os.path.join(settings.SDZ_TUTO_DIR, rep)):
                        for file in files:
                            if file.split('.')[-1]=='tuto':
                                titre = os.path.splitext(file)[0]
                                tuto = os.path.join(root, file)
                            elif file.split('.')[-1]=='zip':
                                images = os.path.join(root, file)
                            elif file.split('.')[-1]in ['png', 'jpg', 'ico', 'jpeg', 'gif']:
                                logo = os.path.join(root, file)

    return (id, titre, tuto, images, logo)
