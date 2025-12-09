from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import PublishableContentFactory


class ListShareableLinksTests(TutorialTestMixin, TestCase):
    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_no_link(self):
        self.client.force_login(self.author)
        response = self.client.get(self.url)
        self.assertContains(response, _("Vous n'avez pas de liens de partage actifs."))
        self.assertContains(response, _("Nouveau lien de partage"))

    def test_one_link(self):
        self.client.force_login(self.author)
        ShareableLink(content=self.content).save()
        response = self.client.get(self.url)
        self.assertContains(response, _("Liens actifs"))
        self.assertContains(response, _("Nouveau lien de partage"))
        self.assertContains(response, '<li class="shareable-link-frame">', count=1)

    def test_two_links(self):
        self.client.force_login(self.author)
        ShareableLink(content=self.content).save()
        ShareableLink(content=self.content).save()
        response = self.client.get(self.url)
        self.assertContains(response, _("Liens actifs"))
        self.assertContains(response, _("Nouveau lien de partage"))
        self.assertContains(response, '<li class="shareable-link-frame">', count=2)
