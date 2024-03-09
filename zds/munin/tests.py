from django.test import TestCase
from django.urls import reverse


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
