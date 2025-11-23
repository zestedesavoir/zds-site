from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.canonical import EditCanonicalLinkForm, EditCanonicalLinkView


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
        self.form_url = reverse("content:edit-canonical-link", kwargs={"pk": self.content.pk})
        self.form_data = {"source": "https://example.com"}
        self.content_data = {"pk": self.content.pk, "slug": self.content.slug}
        self.content_url = reverse("content:view", kwargs=self.content_data)
        self.login_url = reverse("member-login") + "?next=" + self.form_url

    def test_not_authenticated(self):
        self.client.logout()  # ensure no user is authenticated
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)


@override_for_contents()
class WorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user])

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-canonical-link", kwargs={"pk": self.content.pk})
        self.error_messages = EditCanonicalLinkForm.declared_fields["source"].error_messages
        self.error_messages["too_long"] = _("Assurez-vous que cette valeur comporte au plus")
        self.success_message = EditCanonicalLinkView.success_message

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        self.client.force_login(self.author.user)

    def get_test_cases(self):
        return {
            "no_field": {"inputs": {}, "expected_outputs": [self.success_message]},
            "empty": {"inputs": {"source": ""}, "expected_outputs": [self.success_message]},
            "valid_1": {"inputs": {"source": "example.com"}, "expected_outputs": [self.success_message]},
            "valid_2": {"inputs": {"source": "https://example.com"}, "expected_outputs": [self.success_message]},
            "invalid": {"inputs": {"source": "invalid_url"}, "expected_outputs": [self.error_messages["invalid"]]},
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
        self.form_url = reverse("content:edit-canonical-link", kwargs={"pk": self.content.pk})

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        self.client.force_login(self.author.user)

    @patch("zds.tutorialv2.signals.canonical_link_management")
    def test_normal(self, canonical_link_management):
        valid_url = "https://example.com"
        self.client.post(self.form_url, data={"source": valid_url}, follow=True)
        expected = {"source": valid_url, "call_count": 1}
        self.check_effects(expected, canonical_link_management)

    @patch("zds.tutorialv2.signals.canonical_link_management")
    def test_empty(self, canonical_link_management):
        self.client.post(self.form_url, data={"source": ""}, follow=True)
        expected = {"source": "", "call_count": 1}
        self.check_effects(expected, canonical_link_management)

    def check_effects(self, expected_outputs, canonical_link_management):
        self.content.refresh_from_db()
        self.assertEqual(self.content.source, expected_outputs["source"])
        self.assertEqual(canonical_link_management.send.call_count, expected_outputs["call_count"])
