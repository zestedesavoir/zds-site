from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.shareable_links import DeactivateShareableLinkView


class DeactivateShareableLinkTests(TestCase):
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
        self.url = reverse("content:deactivate-shareable-link", kwargs={"id": self.link.id})
        self.redirect_url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, self.redirect_url, target_status_code=200)
        self.assertContains(response, DeactivateShareableLinkView.success_message)
        self.link.refresh_from_db()
        self.assertFalse(self.link.active)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
