# coding: utf-8
from django.core.urlresolvers import reverse

from django.test import TestCase

from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory


class InterventionsTest(TestCase):
    """
    This test uses quite complicated paths to check number of notifications:
    1. Create private topics and do stuff with them
    2. Log the user
    3. Render the home page
    4. Check the number of unread private messages on home page source code
    This because a correct test of this function requires a complete context (or it behave strangely)
    """

    def setUp(self):
        self.author = ProfileFactory()
        self.user = ProfileFactory()
        self.topic = PrivateTopicFactory(author=self.author.user)
        self.topic.participants.add(self.user.user)
        self.post = PrivatePostFactory(
            privatetopic=self.topic,
            author=self.author.user,
            position_in_topic=1)

    def test_interventions_privatetopics(self):

        self.assertTrue(
            self.client.login(
                username=self.author.user.username,
                password='hostel77'
            )
        )
        response = self.client.post(reverse('zds.pages.views.home'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

        self.client.logout()

        self.assertTrue(
            self.client.login(
                username=self.user.user.username,
                password='hostel77'
            )
        )
        response = self.client.post(reverse('zds.pages.views.home'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

    def test_interventions_privatetopics_author_leave(self):

        # profile1 (author) leave topic
        move = self.topic.participants.first()
        self.topic.author = move
        self.topic.participants.remove(move)
        self.topic.save()

        self.assertTrue(
            self.client.login(
                username=self.user.user.username,
                password='hostel77'
            )
        )
        response = self.client.post(reverse('zds.pages.views.home'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)
