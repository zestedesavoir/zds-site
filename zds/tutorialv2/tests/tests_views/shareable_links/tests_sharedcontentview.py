from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.tests.factories import PublishableContentFactory


class DraftViewTests(TestCase):
    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content and a link
        self.content = PublishableContentFactory(author_list=[self.author])
        self.link = ShareableLink(content=self.content)
        self.link.save()

        # Get information to be reused in tests
        self.link_url = reverse("content:shareable-link-view", kwargs={"id": self.link.id})

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_author_inactive(self):
        self.client.force_login(self.author)
        self.link.deactivate()
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, 403)


class BetaViewTests(TestCase):
    def setUp(self):
        self.author = ProfileFactory().user

        # Create a content and a link
        self.content = PublishableContentFactory(author_list=[self.author])
        self.link = ShareableLink(content=self.content, type="BETA")
        self.link.save()

        # Get information to be reused in tests
        self.link_url = reverse("content:shareable-link-view", kwargs={"id": self.link.id})

    def test_not_authenticated_beta(self):
        self.client.logout()
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, 404)
