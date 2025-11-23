from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.thumbnail import EditThumbnailForm, EditThumbnailView


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
        self.form_url = reverse("content:edit-thumbnail", kwargs={"pk": self.content.pk})
        thumbnail = (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")
        self.form_data = {"image": thumbnail}
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
class WorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        self.author = ProfileFactory()
        self.content = PublishableContentFactory(author_list=[self.author.user])

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-thumbnail", kwargs={"pk": self.content.pk})

        self.form_error_messages = EditThumbnailForm.declared_fields["image"].error_messages
        self.view_error_messages = EditThumbnailView.error_messages
        self.success_message = EditThumbnailView.success_message

        # Log in with an authorized user (e.g the author of the content)
        self.client.force_login(self.author.user)

    def get_test_cases(self):
        good_thumbnail = (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")
        humongus_thumbnail = (settings.BASE_DIR / "fixtures" / "image_test.jpg").open("rb")
        return {
            "empty_form": {"inputs": {}, "expected_outputs": [self.form_error_messages["required"]]},
            "empty_fields": {"inputs": {"image": ""}, "expected_outputs": [self.form_error_messages["required"]]},
            "basic_success": {"inputs": {"image": good_thumbnail}, "expected_outputs": [self.success_message]},
            "file_too_large": {
                "inputs": {"image": humongus_thumbnail},
                "expected_outputs": [self.form_error_messages["file_too_large"]],
            },
        }

    def test_form_workflow(self):
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                response = self.client.post(self.form_url, case["inputs"], follow=True)
                for msg in case["expected_outputs"]:
                    self.assertContains(response, escape(msg))


@override_for_contents()
class FunctionalTests(TutorialTestMixin, TestCase):
    """Test the detailed behavior of the feature, such as updates of the database or repositories."""

    def setUp(self):
        self.author = ProfileFactory()
        self.content = PublishableContentFactory(author_list=[self.author.user])
        self.form_url = reverse("content:edit-thumbnail", kwargs={"pk": self.content.pk})
        self.form_data = {"image": (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")}

        self.client.force_login(self.author.user)

    @patch("zds.tutorialv2.signals.thumbnail_management")
    def test_normal(self, thumbnail_management):
        self.assertEqual(self.content.title, self.content.gallery.title)
        start_date = datetime.now()
        self.assertTrue(self.content.update_date < start_date)

        response = self.client.post(self.form_url, self.form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.content.refresh_from_db()

        self.assertIsNotNone(self.content.image)
        self.assertEqual(self.content.gallery.get_images().count(), 1)
        self.assertEqual(thumbnail_management.send.call_count, 1)
