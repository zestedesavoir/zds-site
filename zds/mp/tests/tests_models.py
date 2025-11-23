from math import ceil
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory
from zds.mp.models import (
    NotParticipatingError,
    NotReachableError,
    PrivateTopic,
    is_privatetopic_unread,
    is_reachable,
    mark_read,
)
from zds.mp.tests.factories import PrivatePostFactory, PrivateTopicFactory

# by moment, i wrote the scenario to be simpler


class PrivateTopicTest(TestCase):
    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create the bot accound and add it to the bot group
        self.bot = ProfileFactory().user
        bot_group = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot_group.save()
        self.bot.groups.add(bot_group)

        self.topic1 = PrivateTopicFactory(author=self.user1)
        self.topic1.participants.add(self.user2)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.user1, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.user2, position_in_topic=2)

    def test_get_absolute_url(self):
        url = reverse("mp:view", args=[self.topic1.pk, self.topic1.slug()])

        self.assertEqual(self.topic1.get_absolute_url(), url)

    def test_get_post_count(self):
        self.assertEqual(2, self.topic1.get_post_count())

    def test_get_last_answer(self):
        topic = PrivateTopicFactory(author=self.user2)
        PrivatePostFactory(privatetopic=topic, author=self.user2, position_in_topic=1)

        self.assertEqual(self.post2, self.topic1.get_last_answer())
        self.assertNotEqual(self.post1, self.topic1.get_last_answer())

        self.assertIsNone(topic.get_last_answer())

    def test_first_post(self):
        topic = PrivateTopicFactory(author=self.user2)
        self.assertEqual(self.post1, self.topic1.first_post())
        self.assertIsNone(topic.first_post())

    def test_last_read_post(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.assertEqual(self.post1, self.topic1.last_read_post(self.user1))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        mark_read(self.topic1, user=self.user1)
        self.assertEqual(self.post2, self.topic1.last_read_post(self.user1))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        PrivatePostFactory(privatetopic=self.topic1, author=self.user2, position_in_topic=3)
        self.assertEqual(self.post2, self.topic1.last_read_post(self.user1))

    def test_first_unread_post(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.assertEqual(self.post1, self.topic1.first_unread_post(self.user1))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        mark_read(self.topic1, self.user1)
        post3 = PrivatePostFactory(privatetopic=self.topic1, author=self.user2, position_in_topic=3)

        self.assertEqual(post3, self.topic1.first_unread_post(self.user1))

    def test_one_participant_remaining(self):
        topic2 = PrivateTopicFactory(author=self.user1)
        self.assertFalse(self.topic1.one_participant_remaining())
        self.assertTrue(topic2.one_participant_remaining())

    def test_is_unread(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.assertTrue(self.topic1.is_unread(self.user1))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        mark_read(self.topic1, self.user1)
        self.assertTrue(self.topic1.is_unread(self.user1))  # cache is working
        self.topic1 = PrivateTopic.objects.get(pk=self.topic1.pk)  # get a new object to have an empty cache
        self.assertFalse(self.topic1.is_unread(self.user1))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        PrivatePostFactory(privatetopic=self.topic1, author=self.user2, position_in_topic=3)
        self.assertFalse(self.topic1.is_unread(self.user1))  # cache is working
        self.topic1 = PrivateTopic.objects.get(pk=self.topic1.pk)  # get a new object to have an empty cache
        self.assertTrue(self.topic1.is_unread(self.user1))

    def test_topic_never_read_get_last_read(self):
        """Trying to read last message of a never read Private Topic
        Should return the first message of the Topic"""

        tester = ProfileFactory()
        self.topic1.participants.add(tester.user)
        self.assertEqual(self.topic1.last_read_post(user=tester.user), self.post1)

    def test_is_author(self):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertTrue(self.topic1.is_author(self.user1))
        self.assertFalse(self.topic1.is_author(self.user2))

    def test_set_as_author_same_author(self):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.set_as_author(self.user1)
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])

    def test_set_as_author_new_author(self):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.set_as_author(self.user2)
        self.assertEqual(self.topic1.author, self.user2)
        self.assertEqual(list(self.topic1.participants.all()), [self.user1])

    def test_set_as_author_outsider(self):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        with self.assertRaises(NotParticipatingError):
            self.topic1.set_as_author(self.outsider)

    def test_is_participant(self):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.assertTrue(self.topic1.is_participant(self.user1))
        self.assertTrue(self.topic1.is_participant(self.user2))
        self.assertFalse(self.topic1.is_participant(self.outsider))

    @patch("zds.mp.signals.participant_added")
    def test_add_participant_unreachable_user(self, participant_added):
        self.assertFalse(is_reachable(self.bot))
        with self.assertRaises(NotReachableError):
            self.topic1.add_participant(self.bot)
        self.assertFalse(participant_added.send.called)

    @patch("zds.mp.signals.participant_added")
    def test_add_participant_already_participating(self, participant_added):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.add_participant(self.user2)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.assertFalse(participant_added.send.called)

    @patch("zds.mp.signals.participant_added")
    def test_add_participant_normal(self, participant_added):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.add_participant(self.outsider)
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2, self.outsider])
        self.assertEqual(participant_added.send.call_count, 1)

    @patch("zds.mp.signals.participant_removed")
    def test_remove_participant_not_participating(self, participant_removed):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.remove_participant(self.outsider)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.assertFalse(participant_removed.send.called)

    @patch("zds.mp.signals.participant_removed")
    def test_remove_participant_author(self, participant_removed):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.remove_participant(self.user1)
        self.assertEqual(self.topic1.author, self.user2)
        self.assertEqual(list(self.topic1.participants.all()), [])
        self.assertEqual(participant_removed.send.call_count, 1)

    @patch("zds.mp.signals.participant_removed")
    def test_remove_participant_normal(self, participant_removed):
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [self.user2])
        self.topic1.remove_participant(self.user2)
        self.assertEqual(self.topic1.author, self.user1)
        self.assertEqual(list(self.topic1.participants.all()), [])
        self.assertEqual(participant_removed.send.call_count, 1)


class PrivatePostTest(TestCase):
    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread

        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

    def test_absolute_url(self):
        page = int(ceil(float(self.post1.position_in_topic) / settings.ZDS_APP["forum"]["posts_per_page"]))

        url = f"{self.post1.privatetopic.get_absolute_url()}?page={page}#p{self.post1.pk}"

        self.assertEqual(url, self.post1.get_absolute_url())


class PrivateTopicReadTest(TestCase):
    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread

        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)


class FunctionTest(TestCase):
    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread

        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

    def test_never_privateread(self):
        self.assertTrue(is_privatetopic_unread(self.topic1, self.profile1.user))
        mark_read(self.topic1, self.profile1.user)
        self.assertFalse(is_privatetopic_unread(self.topic1, self.profile1.user))

    @patch("zds.mp.signals.topic_read")
    def test_mark_read(self, topic_read):
        self.assertTrue(self.topic1.is_unread(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        mark_read(self.topic1, self.profile1.user)
        self.assertEqual(topic_read.send.call_count, 1)
        self.assertTrue(self.topic1.is_unread(self.profile1.user))  # cache is working
        self.topic1 = PrivateTopic.objects.get(pk=self.topic1.pk)  # get a new object to have an empty cache
        self.assertFalse(self.topic1.is_unread(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=3)
        self.assertFalse(self.topic1.is_unread(self.profile1.user))  # cache is working
        self.topic1 = PrivateTopic.objects.get(pk=self.topic1.pk)  # get a new object to have an empty cache
        self.assertTrue(self.topic1.is_unread(self.profile1.user))
