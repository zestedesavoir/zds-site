from datetime import datetime

from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory

view_name = "content:edit-conclusion"


@override_for_contents()
class PermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.form_url = reverse(view_name, kwargs={"pk": self.content.pk})
        self.form_data = {"conclusion": "conclusion content"}  # avoids changing the slug
        self.content_data = {"pk": self.content.pk, "slug": self.content.slug}
        self.content_url = reverse("content:view", kwargs=self.content_data)
        self.login_url = reverse("member-login") + "?next=" + self.form_url

    def test_not_authenticated(self):
        """Test that on form submission, unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that on form submission, authors are redirected to the content page."""
        self.client.force_login(self.author)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff(self):
        """Test that on form submission, staffs are redirected to the content page."""
        self.client.force_login(self.staff)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_outsider(self):
        """Test that on form submission, unauthorized users get a 403."""
        self.client.force_login(self.outsider)
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)


@override_for_contents()
class FunctionalTests(TutorialTestMixin, TestCase):
    """Test the detailed behavior of the feature, such as updates of the database or repositories."""

    def setUp(self):
        self.author = ProfileFactory()
        self.content = PublishableContentFactory(author_list=[self.author.user])
        self.form_url = reverse(view_name, kwargs={"pk": self.content.pk})
        self.client.force_login(self.author.user)

    def test_normal(self):
        start_date = datetime.now()
        self.assertTrue(self.content.update_date < start_date)

        new_conclusion = "Ceci n'est pas l'ancienne conclusion"
        response = self.client.post(self.form_url, {"conclusion": new_conclusion}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.content.refresh_from_db()

        # Database update
        self.assertTrue(self.content.update_date > start_date)

        # Update in repository
        versioned_content = self.content.load_version()
        self.assertEqual(versioned_content.get_conclusion(), new_conclusion)

    def test_preview(self):
        some_markdown = "Ceci est un texte avec du **markdown**"
        expected_preview = "Ceci est un texte avec du <strong>markdown</strong>"

        response = self.client.post(
            self.form_url, {"text": some_markdown, "preview": ""}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(200, response.status_code)
        result_string = "".join(str(a, "utf-8") for a in response.streaming_content)
        self.assertIn(expected_preview, result_string, "We need the text to be properly formatted")
