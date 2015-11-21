#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Poll(models.Model):

    class Meta:
        verbose_name = 'Poll'
        verbose_name_plural = 'Polls'
        ordering = ['pubdate']

    title = models.CharField('Titre', max_length=80)
    slug = models.SlugField(max_length=80)
    user = models.ForeignKey(User, verbose_name=_(u'Membre'), db_index=True)
    pubdate = models.DateTimeField('Date de création', auto_now_add=True, db_index=True)
    enddate = models.DateTimeField('Date de fin', null=True, blank=True)
    open = models.BooleanField(default=False)
    anonymous_vote = models.BooleanField('Vote anonyme', default=True)

    def __unicode__(self):
        """Human-readable representation of the Poll model.

        :return: Poll title
        :rtype: unicode
        """
        return self.title

    def get_absolute_url(self):
        """URL of a single Poll.

        :return: Poll object URL
        :rtype: str
        """
        return reverse('poll-details', args=[self.pk])


class Choice(models.Model):

    class Mete:
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'

    choice = models.CharField('Choix', max_length=200)
    poll = models.ForeignKey(Poll, related_name='choices', null=False, blank=False)

    def __unicode__(self):
        """Human-readable representation of the Poll model.

        :return: Choice
        :rtype: unicode
        """
        return self.choice