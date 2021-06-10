from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.tests import TutorialTestMixin


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
        self.assertContains(response, _("Créer un lien de partage"))

    def test_one_link(self):
        self.client.force_login(self.author)
        ShareableLink(content=self.content).save()
        response = self.client.get(self.url)
        self.assertContains(response, _("Liens actifs"))
        self.assertContains(response, _("Créer un lien de partage"))
        self.assertContains(response, '<li class="shareable-link">', count=1)

    def test_two_links(self):
        self.client.force_login(self.author)
        ShareableLink(content=self.content).save()
        ShareableLink(content=self.content).save()
        response = self.client.get(self.url)
        self.assertContains(response, _("Liens actifs"))
        self.assertContains(response, _("Créer un lien de partage"))
        self.assertContains(response, '<li class="shareable-link">', count=2)


class CreateShareableLinkTests(TestCase):
    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.url = reverse("content:create-shareable-link", kwargs={"pk": self.content.pk})
        self.redirect_url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        n_links_before = len(ShareableLink.objects.all())
        data = {"description": "Ceci n'est pas le lien vers La Blague", "expiration": "2042-08-01", "type": "BETA"}
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, self.redirect_url)
        n_links_after = len(ShareableLink.objects.all())
        self.assertEqual(n_links_after, n_links_before + 1)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class EditShareableLinkTests(TestCase):
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
        self.url = reverse("content:edit-shareable-link", kwargs={"id": self.link.id})
        self.redirect_url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        data = {"description": "Ceci n'est pas le lien vers La Blague", "expiration": "2042-08-01", "type": "BETA"}
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, self.redirect_url)
        link = ShareableLink.objects.get(id=self.link.id)
        self.assertEqual(link.description, data["description"])
        self.assertEqual(link.expiration, datetime.strptime(data["expiration"], "%Y-%m-%d"))
        self.assertEqual(link.type, data["type"])

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


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
        response = self.client.post(self.url)
        self.assertRedirects(response, self.redirect_url)
        link = ShareableLink.objects.get(id=self.link.id)
        self.assertFalse(link.active)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class ReactivateShareableLinkTests(TestCase):
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
        self.url = reverse("content:reactivate-shareable-link", kwargs={"id": self.link.id})
        self.redirect_url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url)
        self.assertRedirects(response, self.redirect_url)
        link = ShareableLink.objects.get(id=self.link.id)
        self.assertTrue(link.active)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class DeleteShareableLinkTests(TestCase):
    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create content and links
        self.content = PublishableContentFactory(author_list=[self.author])
        self.link = ShareableLink(content=self.content)
        self.link.save()

        # Get information to be reused in tests
        self.url = reverse("content:delete-shareable-link", kwargs={"id": self.link.id})
        self.redirect_url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url)
        self.assertRedirects(response, self.redirect_url)
        with self.assertRaises(ShareableLink.DoesNotExist):
            ShareableLink.objects.get(id=self.link.id)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class DisplaySharedContentPermissionTest(TestCase):
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
        self.link_url = reverse("content:shareable-link", kwargs={"id": self.link.id})

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
