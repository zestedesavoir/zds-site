# coding: utf-8

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from hashlib import md5

from zds.forum.models import Post, Topic
from zds.tutorial.models import Tutorial


class Profile(models.Model):

    '''Represents an user profile'''
    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
        permissions = (
                ("moderation",u"Moderer un membre"),
                ("show_ip",u"Afficher les IP d'un membre"),
        )

    user = models.ForeignKey(User, unique=True, verbose_name='Utilisateur')
    
    last_ip_address = models.CharField('Adresse IP', max_length=15, blank=True)

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
    
    

    def __unicode__(self):
        '''Textual forum of a profile'''
        return self.user.username

    def get_absolute_url(self):
        '''Absolute URL to the profile page'''
        return '/membres/voir/{0}'.format(self.user.username)

    def get_avatar_url(self):
        '''Avatar URL (using custom URL or Gravatar)'''
        if self.avatar_url:
            return self.avatar_url
        else:
            return 'https://secure.gravatar.com/avatar/{0}?d=identicon'.format(md5(self.user.email).hexdigest())

    def get_post_count(self):
        '''Number of messages posted'''
        return Post.objects.all().filter(author__pk=self.user.pk).count()

    def get_topic_count(self):
        '''Number of threads created'''
        return Topic.objects.all().filter(author=self.user).count()
    
    def get_tuto(self):
        '''Tutorial in draft'''
        return Tutorial.objects.all().filter(authors__in=[self.user]).count()
    
    def get_draft_tuto(self):
        '''Tutorial in draft'''
        return Tutorial.objects.all().filter(authors__in=[self.user], sha_public__isnull=True, sha_draft__isnull=False)
    
    def get_public_tuto(self):
        '''Draft tuto'''
        return Tutorial.objects.all().filter(authors__in=[self.user], sha_public__isnull=False)
    
    def get_validate_tuto(self):
        '''Tutorial in validation'''
        return Tutorial.objects.all().filter(authors__in=[self.user], sha_validation__isnull=False)
    
    def get_beta_tuto(self):
        '''Tutorial in beta'''
        return Tutorial.objects.all().filter(authors__in=[self.user], sha_beta__isnull=False)
    
    def get_is_author(self):
        return False
    
    def get_ip_address(self):
        return Post.objects.all().filter(author=self.user)
    
    
