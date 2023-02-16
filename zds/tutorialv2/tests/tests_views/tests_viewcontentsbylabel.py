from django.test import TestCase
from django.urls import reverse

from zds.tutorialv2.tests.factories import LabelFactory, PublishedContentFactory


class ViewContentsByLabelTests(TestCase):
    def setUp(self):
        self.labels = [LabelFactory(), LabelFactory()]
        self.contents = [PublishedContentFactory(), PublishedContentFactory()]

    def test_page_content(self):
        """Test roughly that what is expected is in the page."""
        response = self.client.get(reverse("content:view-labels"))
        self.assertEqual(response.status_code, 200)
        for label in self.labels:
            self.assertContains(response, label.name)
        for content in self.contents:
            self.assertContains(response, content.title)
