# coding: utf-8
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from hashlib import md5

from zds.forum.models import Post, Topic
from zds.utils.models import Alert
from zds.tutorial.models import Tutorial
from zds.article.models import Article


import uuid


class Profile(models.Model):

    '''Represents an user profile'''
    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
        permissions = (
                ("moderation", u"Modérer un membre"),
                ("show_ip", u"Afficher les IP d'un membre"),
        )

    user = models.ForeignKey(User, unique=True, verbose_name='Utilisateur')
    
    last_ip_address = models.CharField('Adresse IP', max_length=15, blank=True,  null=True)

    site = models.CharField('Site internet', max_length=128, blank=True)
    show_email = models.BooleanField('Afficher adresse mail publiquement',
                                     default=True)

    avatar_url = models.CharField(
        'URL de l\'avatar', max_length=128, null=True, blank=True
    )

    biography = models.TextField('Biographie', blank=True)
    
    karma = models.IntegerField('Karma', default=0)
    
    sign = models.TextField('Signature', blank=True)
    
    show_sign = models.BooleanField('Voir les signatures',
                                     default=True)
    
    hover_or_click = models.BooleanField('Survol ou click ?',
                                     default=True)
    
    can_read = models.BooleanField('Possibilité de lire', default=True)
    end_ban_read = models.DateTimeField('Fin d\'interdiction de lecture', null=True, blank=True)
    
    can_write = models.BooleanField('Possibilité d\'écrire', default=True)
    end_ban_write = models.DateTimeField('Fin d\'interdiction d\'ecrire', null=True, blank=True)

    def __unicode__(self):
        '''Textual forum of a profile'''
        return self.user.username

    def get_absolute_url(self):
        '''Absolute URL to the profile page'''
        return '/membres/voir/{0}'.format(self.user.username)
    
    def get_city(self):
        ''' return physical adress by geolocalisation '''
        try:
            from django.contrib.gis.geoip import GeoIP
            g = GeoIP()
            geo = g.city(self.last_ip_address)
            return u'{0}, {1}'.format(str(geo['city']), str(geo['country_name']))
        except:
            return u'Ankh-Morpork, Discworld'
    
    def get_avatar_url(self):
        '''Avatar URL (using custom URL or Gravatar)'''
        if self.avatar_url:
            return self.avatar_url
        else:
            return 'https://secure.gravatar.com/avatar/{0}?d=identicon'.format(md5(self.user.email).hexdigest())

    def get_post_count(self):
        '''Number of messages posted'''
        return Post.objects.filter(author__pk=self.user.pk).count()

    def get_topic_count(self):
        '''Number of threads created'''
        return Topic.objects.filter(author=self.user).count()
    
    def get_tuto_count(self):
        '''Number of tutos created'''
        return Tutorial.objects.filter(authors__in=[self.user]).count()

    def get_tutos(self):
        '''Get all tutorials of the user'''
        return Tutorial.objects.filter(authors__in = [self.user]).all()
    
    def get_draft_tutos(self):
        '''Tutorial in draft'''
        return Tutorial.objects.filter(authors__in=[self.user], sha_public__isnull=True, sha_draft__isnull=False).all()
    
    def get_public_tutos(self):
        '''Tutorial in public'''
        return Tutorial.objects.filter(authors__in=[self.user], sha_public__isnull=False).all()
    
    def get_validate_tutos(self):
        '''Tutorial in validation'''
        return Tutorial.objects.filter(authors__in=[self.user], sha_validation__isnull=False).all()
    
    def get_beta_tutos(self):
        '''Tutorial in beta'''
        return Tutorial.objects.filter(authors__in=[self.user], sha_beta__isnull=False).all()

    def get_articles(self):
        '''Get all articles of the user'''
        return Article.objects.filter(authors__in=[self.user]).all()
    
    def get_posts(self):
        return Post.objects.filter(author=self.user).all()
    
    def get_invisible_posts_count(self):
        return Post.objects.filter(is_visible=False, author=self.user).count()
    
    def get_alerts_posts_count(self):
        return Alert.objects.filter(author=self.user).count()
    
    def can_read_now(self):
        if self.end_ban_read:
            return self.can_read or (self.end_ban_read < datetime.now())
        else:
            return self.can_read
    
    def can_write_now(self):
        if self.user.is_active:
            if self.end_ban_write:
                return self.can_write or (self.end_ban_write < datetime.now())
            else:
                return self.can_write
        else:
            return False

class TokenForgotPassword(models.Model):
    class Meta:
        verbose_name = 'Token de mot de passe oublié'
        verbose_name_plural = 'Tokens de mots de passe oubliés'

    user = models.ForeignKey(User, verbose_name='Utilisateur')
    token = models.CharField(max_length=100)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        '''Absolute URL to the new password page'''
        return reverse('zds.member.views.new_password')+'?token={0}'.format(self.token)


class TokenRegister(models.Model):
    class Meta:
        verbose_name = 'Token d\'inscription'
        verbose_name_plural = 'Tokens  d\'inscription'

    user = models.ForeignKey(User, verbose_name='Utilisateur')
    token = models.CharField(max_length=100)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        '''Absolute URL to the active account page'''
        return reverse('zds.member.views.active_account')+'?token={0}'.format(self.token)
    
    def __unicode__(self):
        '''Textual forum of a profile'''
        return u"{0} - {1}".format(self.user.username, self.date_end)
            
class Ban(models.Model):
    class Meta:
        verbose_name = 'Sanction'
        verbose_name_plural = 'Sanctions'
        
    user = models.ForeignKey(User, verbose_name='Sanctionné')
    moderator = models.ForeignKey(User, verbose_name='Moderateur',
                                     related_name='bans')
    type = models.CharField('Type',  max_length=15)
    text = models.TextField('Explication de la sanction')
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True)
