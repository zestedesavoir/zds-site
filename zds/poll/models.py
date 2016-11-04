#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _


class Poll(models.Model):

    class Meta:
        verbose_name = _(u'Sondage')
        verbose_name_plural = _(u'Sondages')
        ordering = ['-pubdate']

    title = models.CharField(_(u'Titre'), max_length=80)
    slug = models.SlugField(max_length=80)
    author = models.ForeignKey(User, verbose_name=_(u'Auteur'),
                               related_name=_(u'polls'), db_index=True)
    pubdate = models.DateTimeField(_(u'Date de création'), auto_now_add=True, db_index=True)
    end_date = models.DateTimeField(_(u'Date de fin'), null=True, blank=True)

    activate = models.BooleanField(default=True)
    anonymous_vote = models.BooleanField(_(u'Vote anonyme'), default=True)

    multiple_vote = models.BooleanField(_(u'Vote multiple'), default=False)

    def __unicode__(self):
        """
        Human-readable representation of the Poll model.
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

    def get_user_vote_objects(self, user):
        """
        Get all the vote for a given user
        :param user:
        :return: A queryset of Vote
        """
        return self.get_vote_class().objects.filter(poll=self, user=user)

    def get_user_vote_dict(self, user):
        """
        Get all the vote for a given user
        :param user:
        :return: A dict
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
        if self.end_date:
            return self.end_date < datetime.datetime.now()
        else:
            return False

    def get_vote_class(self):
        if self.multiple_vote:
            return MultipleVote
        elif not self.multiple_vote:
            return UniqueVote
        raise TypeError


class Choice(models.Model):

    class Meta:
        verbose_name = _(u'Choix')
        verbose_name_plural = _(u'Choix')

    choice = models.CharField(_(u'Choix'), max_length=200)
    poll = models.ForeignKey(Poll, related_name='choices', null=False, blank=False, verbose_name=_(u'sondage'))

    def __unicode__(self):
        """
        Human-readable representation of the Choice model.
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

    def get_users(self):
        """
        :return: Users
        :rtype: a list
        """
        return [Vote.user for Vote in self.poll.get_vote_class().objects.filter(choice=self, poll=self.poll)]

    def set_user_vote(self, user):
        if self.poll.multiple_vote:
            UniqueVote.objects.update_or_create(user=user, choice=self, poll=self.poll)
        elif not self.poll.multiple_vote:
            MultipleVote.objects.update_or_create(user=user, choice=self, poll=self.poll)


class Vote(models.Model):

    class Meta:
        verbose_name = _(u'Vote')
        verbose_name_plural = _(u'Votes')
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
        verbose_name = _(u'Vote unique')
        verbose_name_plural = _(u'Votes uniques')
        unique_together = (('user', 'choice'), ('user', 'poll'))


class MultipleVote(Vote):
    """
    Multiple vote allow member to vote for one or more choices
    """

    class Meta:
        verbose_name = _(u'Votes multiple')
        verbose_name_plural = _(u'Multiple Votes')
        unique_together = ('user', 'choice', 'poll')
