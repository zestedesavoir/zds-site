#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django.db import models
from django import forms
from django.db.models import Count, Sum
from django.utils.translation import ugettext_lazy as _

UNIQUE_VOTE_KEY = 'u'
MULTIPLE_VOTE_KEY = 'm'
RANGE_VOTE_KEY = 'r'

RANGES = (
    (2, 'Très favorable'),
    (1, 'Favorable'),
    (0, 'Indifférent'),
    (-1, 'Hostile'),
    (-2, 'Très hostile')
)


class Poll(models.Model):

    class Meta:
        verbose_name = 'Sondage'
        verbose_name_plural = 'Sondages'
        ordering = ['-pubdate']

    TYPE_VOTE_CHOICES = (
        (UNIQUE_VOTE_KEY, 'Vote unique'),
        (MULTIPLE_VOTE_KEY, 'Vote multiple'),
        (RANGE_VOTE_KEY, 'Vote par valeurs')
    )

    title = models.CharField('Titre', max_length=80)
    slug = models.SlugField(max_length=80)
    user = models.ForeignKey(User, verbose_name=_(u'Membre'), db_index=True)
    pubdate = models.DateTimeField(_(u'Date de création'), auto_now_add=True, db_index=True)
    enddate = models.DateTimeField(_(u'Date de fin'), null=True, blank=True)

    open = models.BooleanField(default=False)
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
        return self.get_vote_class().objects.filter(poll=self, user=user).values()

    def get_vote_form(self, data=None, **kw):
        return self.get_vote_class().get_form(self, data, **kw)

    def get_vote_class(self):
        if self.type_vote == MULTIPLE_VOTE_KEY:
            return MultipleVote
        elif self.type_vote == UNIQUE_VOTE_KEY:
            return UniqueVote
        elif self.type_vote == RANGE_VOTE_KEY:
            return RangeVote
        return UniqueVote


class Choice(models.Model):

    class Meta:
        verbose_name = 'Choix'
        verbose_name_plural = 'Choix'

    choice = models.CharField('Choix', max_length=200)
    poll = models.ForeignKey(Poll, related_name='choices', null=False, blank=False)

    def __unicode__(self):
        """Human-readable representation of the Poll model.

        :return: Choice
        :rtype: unicode
        """
        return self.choice

    def get_votes_count(self):
        count = self.poll.get_vote_class().objects.filter(choice=self, poll=self.poll).count()
        return count

    def get_votes_score(self):
        score = 0
        if self.poll.type_vote == UNIQUE_VOTE_KEY or self.poll.type_vote == MULTIPLE_VOTE_KEY:
            score = self.poll.get_vote_class().objects.filter(choice=self, poll=self.poll).count()
        elif self.poll.type_vote == RANGE_VOTE_KEY:
            result = RangeVote.objects.filter(choice=self, poll=self.poll).values('choice').annotate(Sum('range'))
            if result:
                score = result[0]['range__sum']
        return score


class Vote(models.Model):

    class Meta:
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        unique_together = ('user', 'choice')
        abstract = True

    poll = models.ForeignKey(Poll)
    choice = models.ForeignKey(Choice, blank=False)
    user = models.ForeignKey(User)

    @staticmethod
    def get_form(poll, data=None, **kw):
        raise NotImplementedError


class UniqueVote(Vote):
    """
    Unique vote allow member to vote only for one choice
    """

    class Meta:
        verbose_name = 'Vote unique'
        verbose_name_plural = 'Votes uniques'
        unique_together = (('user', 'choice'), ('user', 'poll'))

    @staticmethod
    def get_form(poll, data=None, **kw):
        from zds.poll.forms import UniqueVoteForm
        return UniqueVoteForm(poll, data=data, **kw)


class MultipleVote(Vote):
    """
    Multiple vote allow member to vote for one or more choices
    """

    class Meta:
        verbose_name = 'Votes multiple'
        verbose_name_plural = 'Multiple Votes'
        unique_together = ('user', 'choice', 'poll')

    @staticmethod
    def get_form(poll, data=None, **kw):
        from zds.poll.forms import MultipleVoteForm
        return MultipleVoteForm(poll, data=data, **kw)


class RangeVote(Vote):

    class Meta:
        verbose_name = 'Vote par valeurs'
        verbose_name_plural = 'Votes par valeurs'
        unique_together = ('user', 'choice', 'poll')

    range = models.IntegerField(choices=RANGES, blank=False)

    @staticmethod
    def get_form(poll, data=None, **kw):
        from zds.poll.forms import RangeVoteModelForm, RangeVoteFormSet
        if data:
            range_vote_formset = forms.modelformset_factory(
                RangeVote,
                form=RangeVoteModelForm,
                formset=RangeVoteFormSet
            )
            return range_vote_formset(poll=poll, data=data)
        else:
            initial_data = []
            choices = poll.choices.all()
            count_choices = len(choices)

            # Check if there is some initial data
            kw_initial = kw.get('initial')
            initial_range = {}
            if kw_initial:
                for initial_choice in kw_initial:
                    initial_range[initial_choice['choice_id']] = initial_choice['range']

            for choice in choices:
                if kw_initial:
                    range = initial_range[choice.pk]
                else:
                    # Par default : indifférent
                    range = 0

                initial_data.append(
                    {
                        'choice': choice,
                        'range': range,
                    }
                )
            range_vote_formset = forms.modelformset_factory(
                RangeVote,
                form=RangeVoteModelForm,
                formset=RangeVoteFormSet,
                extra=count_choices,
                max_num=count_choices,
            )
            return range_vote_formset(initial=initial_data, queryset=RangeVote.objects.none())
