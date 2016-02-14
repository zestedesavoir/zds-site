# coding: utf-8

from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.member.factories import ProfileFactory


class PollTests(TestCase):

    def test_success_list_poll(self):
        """
        To test the Poll's list of a user.
        """

        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('poll-list'))

        self.assertEqual(200, response.status_code)

    def test_failure_list_poll_with_unauthenticated_user(self):
        response = self.client.get(reverse('poll-list'))

        self.assertEqual(302, response.status_code)

    def test_success_new_poll(self):
        """
        To test the new poll page.
        """

        profile = ProfileFactory()
        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('poll-new'))

        self.assertEqual(200, response.status_code)

    def test_failure_new_poll_with_unauthenticated_user(self):
        response = self.client.get(reverse('poll-new'))

        self.assertEqual(302, response.status_code)