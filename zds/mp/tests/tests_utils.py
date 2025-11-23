from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory
from zds.mp.models import PrivateTopic


class MpUtilTest(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user1.profile.email_for_answer = True
        self.user1.profile.email_for_new_mp = False
        self.user1.profile.save()

        self.user2 = ProfileFactory().user
        self.user2.profile.email_for_answer = True
        self.user2.profile.email_for_new_mp = False
        self.user2.profile.save()

        self.user3 = ProfileFactory().user
        self.user3.profile.email_for_answer = True
        self.user3.profile.email_for_new_mp = True
        self.user3.profile.save()

        self.user4 = ProfileFactory().user
        self.user4.profile.email_for_answer = False
        self.user4.profile.email_for_new_mp = False
        self.user4.profile.save()

        self.user5 = ProfileFactory().user
        self.user5.profile.email_for_answer = False
        self.user5.profile.email_for_new_mp = True
        self.user5.profile.save()

        # Login as profile1
        self.client.force_login(self.user1)

        # Save bot group
        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

    def test_new_mp_email(self):
        response = self.client.post(
            reverse("mp:create"),
            {
                "participants": self.user2.username
                + ", "
                + self.user3.username
                + ", "
                + self.user4.username
                + ", "
                + self.user5.username,
                "title": "title",
                "subtitle": "subtitle",
                "text": "text",
            },
            follow=True,
        )

        # Assert MP have been sent
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.all().count())

        should_receive_response = [self.user2.email, self.user3.email, self.user5.email]

        # Check everyone receive a MP, except op
        self.assertEqual(len(mail.outbox), len(should_receive_response))

        for response in mail.outbox:
            self.assertTrue(self.user1.username in response.body)
            self.assertIn(response.to[0], should_receive_response)

        PrivateTopic.objects.all().delete()

    def test_answer_mp_email(self):
        # Create a MP
        self.client.post(
            reverse("mp:create"),
            {
                "participants": self.user2.username
                + ", "
                + self.user3.username
                + ", "
                + self.user4.username
                + ", "
                + self.user5.username,
                "title": "title",
                "subtitle": "subtitle",
                "text": "text",
            },
            follow=True,
        )

        mail.outbox = []
        self.client.logout()
        self.client.force_login(self.user2)

        # Add an answer
        topic1 = PrivateTopic.objects.get()
        self.client.post(
            reverse("mp:answer", args=[topic1.pk, topic1.slug()]),
            {"text": "answer", "last_post": topic1.last_message.pk},
            follow=True,
        )

        # Check user1 receive mails
        should_receive_response = [self.user1.email]
        # Check user5 does not receive mails
        should_not_receive_response = [self.user5.email]

        self.assertEqual(len(mail.outbox), len(should_receive_response))

        for response in mail.outbox:
            self.assertTrue(self.user2.username in response.body)
            self.assertIn(response.to[0], should_receive_response)
            self.assertFalse(response.to[0] in should_not_receive_response)

        PrivateTopic.objects.all().delete()

        self.client.logout()
        self.client.force_login(self.user1)
