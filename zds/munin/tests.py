from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory


class Munin(TestCase):
    def setUp(self):
        base_names = [
            "base:total-users",
            "base:active-users",
            "base:total-sessions",
            "base:active-sessions",
            "base:db-performance",
            "total-topics",
            "total-posts",
            "total-mp",
            "total-tutorial",
            "total-articles",
            "total-opinions",
        ]
        self.routes = [f"munin:{base_name}" for base_name in base_names]

    def test_routes(self):
        for route in self.routes:
            with self.subTest(msg=route):
                url = reverse(route)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_sessions(self):
        """Makes sure the sessions are correctly counted in Munin data."""
        response = self.client.get(reverse("munin:base:active-sessions"))
        self.assertEqual(response.content.decode(), "sessions 0")

        response = self.client.get(reverse("munin:base:total-sessions"))
        self.assertEqual(response.content.decode(), "sessions 0")

        profile = ProfileFactory()
        self.client.force_login(profile.user)

        response = self.client.get(reverse("munin:base:active-sessions"))
        self.assertEqual(response.content.decode(), "sessions 1")

        response = self.client.get(reverse("munin:base:total-sessions"))
        self.assertEqual(response.content.decode(), "sessions 1")
