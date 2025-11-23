from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory


class SessionManagementTests(TestCase):
    def test_anonymous_cannot_access(self):
        self.client.logout()

        response = self.client.get(reverse("list-sessions"))
        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("list-sessions"))

        response = self.client.post(reverse("delete-session"))
        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("delete-session"))

    def test_user_can_access(self):
        profile = ProfileFactory()
        self.client.force_login(profile.user)

        response = self.client.get(reverse("list-sessions"))
        self.assertEqual(response.status_code, 200)

        session_key = self.client.session.session_key
        response = self.client.post(reverse("delete-session"), {"session_key": session_key})
        self.assertRedirects(response, reverse("list-sessions"))
