from django.test import TestCase
from django.urls import reverse


class ApiViewTests(TestCase):
    def test_url_api_docs_page(self):
        result = self.client.get(
            reverse("api:docs"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_api_docs_data(self):
        # This is the URL called by AJAX to show API routes in the API
        # documentation page.
        result = self.client.get(reverse("api:docs", query={"format": "openapi"}))

        self.assertEqual(result.status_code, 200)
        self.assertGreater(len(result.data["paths"]), 0)
