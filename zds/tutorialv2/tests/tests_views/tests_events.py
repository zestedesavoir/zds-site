from django.test import TestCase

from django.urls import reverse

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory
from zds.tutorialv2.tests import override_for_contents, TutorialTestMixin


@override_for_contents()
class EventListPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.events_list_url = reverse("content:events", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.events_list_url

    def test_not_authenticated(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated
        response = self.client.get(self.events_list_url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that authors have access to the page."""
        self.client.force_login(self.author)
        response = self.client.get(self.events_list_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_staff(self):
        """Test that staffs have access to the page."""
        self.client.force_login(self.staff)
        response = self.client.get(self.events_list_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_outsider(self):
        """Test that unauthorized users get a 403."""
        self.client.force_login(self.outsider)
        response = self.client.get(self.events_list_url)
        self.assertEquals(response.status_code, 403)
