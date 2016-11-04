# coding: utf-8

from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.member.factories import ProfileFactory
from zds.poll.factories import PollFactory, ChoiceFactory, UniqueVoteFactory, MultipleVoteFactory
from zds.poll.models import UniqueVote, MultipleVote


class PollTest(TestCase):

    def setUp(self):

        self.profile = ProfileFactory()
        self.profile2 = ProfileFactory()

        self.poll = PollFactory(author=self.profile.user)
        self.poll2 = PollFactory(author=self.profile.user)
        self.poll2.multiple_vote = True

        self.choice = ChoiceFactory(poll=self.poll)
        self.choice2 = ChoiceFactory(poll=self.poll2)
        self.choice3 = ChoiceFactory(poll=self.poll2)

        self.unique_vote = UniqueVoteFactory(poll=self.poll, choice=self.choice, user=self.profile.user)
        self.unique_vote2 = UniqueVoteFactory(poll=self.poll, choice=self.choice, user=self.profile2.user)

        self.multiple_vote = MultipleVoteFactory(poll=self.poll2, choice=self.choice2, user=self.profile.user)
        self.multiple_vote2 = MultipleVoteFactory(poll=self.poll2, choice=self.choice3, user=self.profile.user)

    def test_unicode(self):
        self.assertEqual(self.poll.__unicode__(), self.poll.title)

    def test_absolute_url(self):
        url = reverse('poll-details', args=[self.poll.pk])

        self.assertEqual(self.poll.get_absolute_url(), url)

    def test_get_count_user(self):
        self.assertEqual(self.poll.get_count_user(), 2)

        self.unique_vote2.delete()
        self.assertEqual(self.poll.get_count_user(), 1)

    def test_get_user_vote_objects(self):
        self.assertTrue(self.unique_vote in self.poll.get_user_vote_objects(user=self.profile.user))

        self.assertTrue(self.multiple_vote in self.poll2.get_user_vote_objects(user=self.profile.user))
        self.assertTrue(self.multiple_vote2 in self.poll2.get_user_vote_objects(user=self.profile.user))

    def test_is_open(self):
        self.assertEqual(self.poll.is_open(), True)

        self.poll.activate = False
        self.assertEqual(self.poll.is_open(), False)

    def test_is_over(self):
        self.assertEqual(self.poll.is_over(), False)

        self.poll.end_date = datetime.now()
        self.assertEqual(self.poll.is_over(), True)

    def test_get_vote_class(self):
        self.assertEqual(self.poll.get_vote_class(), UniqueVote)

        self.poll.multiple_vote = True
        self.assertEqual(self.poll.get_vote_class(), MultipleVote)


class ChoiceTest(TestCase):

    def setUp(self):
        self.profile = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()

        self.poll = PollFactory(author=self.profile.user)
        self.poll2 = PollFactory(author=self.profile.user)
        self.poll2.multiple_vote = True

        self.choice = ChoiceFactory(poll=self.poll)

        self.unique_vote = UniqueVoteFactory(poll=self.poll, choice=self.choice, user=self.profile.user)
        self.unique_vote2 = UniqueVoteFactory(poll=self.poll, choice=self.choice, user=self.profile2.user)

    def test_unicode(self):
        self.assertEqual(self.choice.__unicode__(), self.choice.choice)

    def test_get_count_votes(self):
        self.assertEqual(self.choice.get_count_votes(), 2)

        self.unique_vote2.delete()
        self.assertEqual(self.choice.get_count_votes(), 1)
