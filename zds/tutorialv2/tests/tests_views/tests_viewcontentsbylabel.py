from django.test import TestCase
from django.urls import reverse

from zds.tutorialv2.tests.factories import LabelFactory, PublishedContentFactory


class ViewContentsByLabelTests(TestCase):
    def setUp(self):
        self.content_with_label_1 = PublishedContentFactory()
        self.content_with_label_2 = PublishedContentFactory()
        self.content_without_label = PublishedContentFactory()
        self.label = LabelFactory()
        self.content_with_label_1.labels.add(self.label)
        self.content_with_label_2.labels.add(self.label)

    def test_content_list_with_label(self):
        url = reverse("content:view-labels", kwargs={"slug": self.label.slug})
        response = self.client.get(url)
        self.assertContains(response, self.content_with_label_1.title)
        self.assertContains(response, self.content_with_label_2.title)
        self.assertNotContains(response, self.content_without_label.title)

    def test_content_list_without_label(self):
        other_label = LabelFactory()
        url = reverse("content:view-labels", kwargs={"slug": other_label.slug})
        response = self.client.get(url)
        self.assertNotContains(response, self.content_with_label_1.title)
        self.assertNotContains(response, self.content_with_label_2.title)
        self.assertNotContains(response, self.content_without_label.title)

    def test_invalid_slug_returns_404(self):
        invalid_slug = "invalid-slug"
        url = reverse("content:view-labels", kwargs={"slug": invalid_slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
