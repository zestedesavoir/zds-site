# coding: utf-8

from django.test import TestCase

from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.utils.templatetags.interventions import interventions_privatetopics


class InterventionsTest(TestCase):

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
        result = interventions_privatetopics(self.author)
        self.assertEqual(result['total'], 1)

        result = interventions_privatetopics(self.user)
        self.assertEqual(result['total'], 1)

    def test_interventions_privatetopics_author_leave(self):

        # profile1 (author) leave topic
        move = self.topic.participants.first()
        self.topic.author = move
        self.topic.participants.remove(move)
        self.topic.save()

        result = interventions_privatetopics(self.user)
        self.assertEqual(result['total'], 1)
