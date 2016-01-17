#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _


UNIQUE_VOTE_KEY = 'u'
MULTIPLE_VOTE_KEY = 'm'


class Poll(models.Model):

    class Meta:
        verbose_name = 'Sondage'
        verbose_name_plural = 'Sondages'
        ordering = ['-pubdate']

    TYPE_VOTE_CHOICES = (
        (UNIQUE_VOTE_KEY, 'Vote unique'),
        (MULTIPLE_VOTE_KEY, 'Vote multiple'),
    )

    title = models.CharField('Titre', max_length=80)
    slug = models.SlugField(max_length=80)
    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='polls', db_index=True)
    pubdate = models.DateTimeField(_(u'Date de création'), auto_now_add=True, db_index=True)
    enddate = models.DateTimeField(_(u'Date de fin'), null=True, blank=True)

    activate = models.BooleanField(default=True)
    anonymous_vote = models.BooleanField(_(u'Vote anonyme'), default=True)

    type_vote = models.CharField('Type de vote', max_length=1, choices=TYPE_VOTE_CHOICES, default=UNIQUE_VOTE_KEY)

    def __unicode__(self):
        """Human-readable representation of the Poll model.

        :return: Poll title
        :rtype: unicode
        """
        return self.title

    def get_absolute_url(self):
        """
        URL of a single Poll.
        :return: Poll object URL
        :rtype: str
        """
        return reverse('poll-details', args=[self.pk])

    def get_count_user(self):
        """
        :return: The number of user who has voted
        :rtype int
        """
        count = self.get_vote_class().objects.filter(poll=self).values('poll').annotate(Count('user', distinct=True))
        if count:
            return count[0]['user__count']
        else:
            return 0

    def get_user_vote(self, user):
        """
        Get all the vote for a given user
        :param user:
        :return:
        """
        return self.get_vote_class().objects.filter(poll=self, user=user).values()

    def is_open(self):
        """
        Determin if a poll is open according
        to the field activate and the end date
        :return:
        """
        return self.activate and not self.is_over()

    def is_over(self):
        """
        Is date past ?
        """
        if self.enddate:
            return self.enddate < datetime.datetime.now()
        else:
            return False

    def get_vote_class(self):
        if self.type_vote == MULTIPLE_VOTE_KEY:
            return MultipleVote
        elif self.type_vote == UNIQUE_VOTE_KEY:
            return UniqueVote
        raise TypeError


class Choice(models.Model):

    class Meta:
        verbose_name = 'Choix'
        verbose_name_plural = 'Choix'

    choice = models.CharField('Choix', max_length=200)
    poll = models.ForeignKey(Poll, related_name='choices', null=False, blank=False)

    def __unicode__(self):
        """Human-readable representation of the Choice model.

        :return: Choice
        :rtype: unicode
        """
        return self.choice

    def get_count_votes(self):
        """
        :return: The count of votes for this choice
        :rtype: int
        """
        count = self.poll.get_vote_class().objects.filter(choice=self, poll=self.poll).count()
        return count


class Vote(models.Model):

    class Meta:
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        unique_together = ('user', 'choice')
        abstract = True

    poll = models.ForeignKey(Poll)
    choice = models.ForeignKey(Choice, blank=False)
    user = models.ForeignKey(User)


class UniqueVote(Vote):
    """
    Unique vote allow member to vote only for one choice
    """

    class Meta:
        verbose_name = 'Vote unique'
        verbose_name_plural = 'Votes uniques'
        unique_together = (('user', 'choice'), ('user', 'poll'))


class MultipleVote(Vote):
    """
    Multiple vote allow member to vote for one or more choices
    """

    class Meta:
        verbose_name = 'Votes multiple'
        verbose_name_plural = 'Multiple Votes'
        unique_together = ('user', 'choice', 'poll')
