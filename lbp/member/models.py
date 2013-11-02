# coding: utf-8

from hashlib import md5

from django.db import models
from django.contrib.auth.models import User

from lbp.forum.models import Post, Topic

class Profile(models.Model):

    '''Represents an user profile'''
    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    user = models.ForeignKey(User, unique=True, verbose_name='Utilisateur')

    site = models.CharField('Site internet', max_length=128, blank=True)
    show_email = models.BooleanField('Afficher adresse mail publiquement',
                                     default=True)

    avatar_url = models.CharField(
        'URL de l\'avatar', max_length=128, null=True, blank=True
    )

    biography = models.TextField('Biographie', blank=True)

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