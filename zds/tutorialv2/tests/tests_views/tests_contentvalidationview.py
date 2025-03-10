from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory, ValidationFactory
from zds.tutorialv2.tests.utils import request_validation


@override_for_contents()
class PermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create a content and put it in validation
        self.author = ProfileFactory().user
        content = PublishableContentFactory(author_list=[self.author])
        request_validation(content)

        # Data about the tested route
        url_args = {"pk": content.pk, "slug": content.slug}
        self.target_url = reverse("content:validation-view", kwargs=url_args)
        self.login_url = reverse("member-login") + "?next=" + self.target_url

    def test_not_authenticated(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated
        response = self.client.get(self.target_url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that authors can reach the page."""
        self.client.force_login(self.author)
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_staff(self):
        """Test that staffs can reach the page."""
        staff = StaffProfileFactory().user
        self.client.force_login(staff)
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_outsider(self):
        """Test that unauthorized users get a 403."""
        outsider = ProfileFactory().user
        self.client.force_login(outsider)
        response = self.client.get(self.target_url)
        self.assertEqual(response.status_code, 403)


@override_for_contents()
class FunctionalTests(TutorialTestMixin, TestCase):
    """Test the behavior of the feature."""

    def setUp(self):
        # Create a content and put it in validation
        self.author = StaffProfileFactory().user
        content = PublishableContentFactory(author_list=[self.author])
        request_validation(content)

        # Data about the tested route
        url_args = {"pk": content.pk, "slug": content.slug}
        self.target_url = reverse("content:validation-view", kwargs=url_args)

    def test_validation_actions_shown(self):
        """Test that the validation page shows the validation actions."""
        self.client.force_login(self.author)
        response = self.client.get(self.target_url)
        self.assertContains(response, "<h3>Validation</h3>")
