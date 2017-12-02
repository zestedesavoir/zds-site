from django.test import TestCase
from django.core.urlresolvers import reverse
from math import ceil

from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.mp.models import mark_read, is_privatetopic_unread
from django.conf import settings

# by moment, i wrote the scenario to be simpler


class PrivateTopicTest(TestCase):

    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread

        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

    def test_absolute_url(self):
        url = reverse('private-posts-list', args=[self.topic1.pk, self.topic1.slug()])

        self.assertEqual(self.topic1.get_absolute_url(), url)

    def test_post_count(self):
        self.assertEqual(2, self.topic1.get_post_count())

    def test_get_last_answer(self):
        topic = PrivateTopicFactory(author=self.profile2.user)
        PrivatePostFactory(
            privatetopic=topic,
            author=self.profile2.user,
            position_in_topic=1)

        self.assertEqual(self.post2, self.topic1.get_last_answer())
        self.assertNotEqual(self.post1, self.topic1.get_last_answer())

        self.assertIsNone(topic.get_last_answer())

    def test_first_post(self):
        topic = PrivateTopicFactory(author=self.profile2.user)
        self.assertEqual(self.post1, self.topic1.first_post())
        self.assertIsNone(topic.first_post())

    def test_last_read_post(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.assertEqual(
            self.post1,
            self.topic1.last_read_post(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        mark_read(self.topic1, user=self.profile1.user)
        self.assertEqual(
            self.post2,
            self.topic1.last_read_post(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=3)
        self.assertEqual(
            self.post2,
            self.topic1.last_read_post(self.profile1.user))

    def test_first_unread_post(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.assertEqual(
            self.post1,
            self.topic1.first_unread_post(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        mark_read(self.topic1, self.profile1.user)
        post3 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=3)

        self.assertEqual(
            post3,
            self.topic1.first_unread_post(self.profile1.user))

    def test_alone(self):
        topic2 = PrivateTopicFactory(author=self.profile1.user)
        self.assertFalse(self.topic1.alone())
        self.assertTrue(topic2.alone())

    def test_never_read(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread
        self.assertTrue(self.topic1.is_unread(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        mark_read(self.topic1, self.profile1.user)
        self.assertFalse(self.topic1.is_unread(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=3)

        self.assertTrue(self.topic1.is_unread(self.profile1.user))

    def test_topic_never_read_get_last_read(self):
        """ Trying to read last message of a never read Private Topic
        Should return the first message of the Topic """

        tester = ProfileFactory()
        self.topic1.participants.add(tester.user)
        self.assertEqual(self.topic1.last_read_post(user=tester.user), self.post1)


class PrivatePostTest(TestCase):

    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread

        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

    def test_absolute_url(self):
        page = int(
            ceil(
                float(
                    self.post1.position_in_topic) /
                settings.ZDS_APP['forum']['posts_per_page']))

        url = '{0}?page={1}#p{2}'.format(
            self.post1.privatetopic.get_absolute_url(),
            page,
            self.post1.pk)

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
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)


class FunctionTest(TestCase):

    def setUp(self):
        # scenario - topic1 :
        # post1 - user1 - unread
        # post2 - user2 - unread

        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

    def test_never_privateread(self):
        self.assertTrue(is_privatetopic_unread(self.topic1, self.profile1.user))
        mark_read(self.topic1, self.profile1.user)
        self.assertFalse(is_privatetopic_unread(self.topic1, self.profile1.user))

    def test_mark_read(self):
        self.assertTrue(self.topic1.is_unread(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        mark_read(self.topic1, self.profile1.user)
        self.assertFalse(self.topic1.is_unread(self.profile1.user))

        # scenario - topic1 :
        # post1 - user1 - read
        # post2 - user2 - read
        # post3 - user2 - unread
        PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=3)
        self.assertTrue(self.topic1.is_unread(self.profile1.user))
