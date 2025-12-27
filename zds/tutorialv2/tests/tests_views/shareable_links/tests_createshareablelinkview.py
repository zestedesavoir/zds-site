from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tests.common import ZdsTestCase as TestCase
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.tests.factories import PublishableContentFactory


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
        n_links_before = ShareableLink.objects.all().count()
        data = {"description": "Ceci n'est pas le lien vers La Blague", "expiration": "2042-08-01", "type": "BETA"}
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, self.redirect_url, target_status_code=200)
        n_links_after = ShareableLink.objects.all().count()
        self.assertEqual(n_links_after, n_links_before + 1)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
