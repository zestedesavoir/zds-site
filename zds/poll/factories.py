# coding: utf-8

from datetime import datetime, timedelta

import factory

from zds.poll.models import Poll, Choice, UniqueVote, MultipleVote


class PollFactory(factory.DjangoModelFactory):

    class Meta:
        model = Poll

    title = 'Nancy ou Metz ?'
    end_date = datetime.now() + timedelta(days=5)


class ChoiceFactory(factory.DjangoModelFactory):

    class Meta:
        model = Choice

    choice = 'Nancy'


class UniqueVoteFactory(factory.DjangoModelFactory):

    class Meta:
        model = UniqueVote


class MultipleVoteFactory(factory.DjangoModelFactory):

    class Meta:
        model = MultipleVote
