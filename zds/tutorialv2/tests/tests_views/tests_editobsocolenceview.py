from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.obsolescence import EditObsolescenceView


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
        self.form_url = reverse("content:edit-obsolescence", kwargs={"pk": self.content.pk})
        self.form_data = {"is_obsolete": True, "text": "Ce contenu est déprécié."}
        self.content_data = {"pk": self.content.pk, "slug": self.content.slug}
        self.content_url = reverse("content:view", kwargs=self.content_data)
        self.login_url = reverse("member-login") + "?next=" + self.form_url

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Authors shall not be able to edit obsolescence (staff only)."""
        self.client.force_login(self.author)
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)

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
        self.staff = StaffProfileFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.staff.user])

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-obsolescence", kwargs={"pk": self.content.pk})
        self.success_message = EditObsolescenceView.success_message

        # Log in with an authorized user to perform the tests
        self.client.force_login(self.staff.user)

    def get_test_cases(self):
        return {
            "no_field": {"inputs": {}, "expected_outputs": [self.success_message]},
            "not_obsolete": {"inputs": {"is_obsolete": False, "text": ""}, "expected_outputs": [self.success_message]},
            "obsolete_no_text": {
                "inputs": {"is_obsolete": True, "text": ""},
                "expected_outputs": [self.success_message],
            },
            "obsolete_with_text": {
                "inputs": {"is_obsolete": True, "text": "Ce contenu est déprécié."},
                "expected_outputs": [self.success_message],
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
        self.staff = StaffProfileFactory()
        self.content = PublishableContentFactory(author_list=[self.staff.user])
        self.form_url = reverse("content:edit-obsolescence", kwargs={"pk": self.content.pk})

        # Log in with an authorized user to perform the tests
        self.client.force_login(self.staff.user)

    @patch("zds.tutorialv2.signals.obsolescence_management")
    def test_mark_as_obsolete(self, obsolescence_management):
        self.client.post(self.form_url, data={"is_obsolete": True, "text": "Contenu déprécié."}, follow=True)
        self.check_effects(
            {"is_obsolete": True, "text": "Contenu déprécié.", "call_count": 1},
            obsolescence_management,
        )

    @patch("zds.tutorialv2.signals.obsolescence_management")
    def test_unmark_as_obsolete(self, obsolescence_management):
        self.client.post(self.form_url, data={"is_obsolete": False, "text": ""}, follow=True)
        self.check_effects(
            {"is_obsolete": False, "text": "", "call_count": 1},
            obsolescence_management,
        )

    @patch("zds.tutorialv2.signals.obsolescence_management")
    def test_empty(self, obsolescence_management):
        self.client.post(self.form_url, data={}, follow=True)
        self.check_effects(
            {"is_obsolete": False, "text": "", "call_count": 1},
            obsolescence_management,
        )

    def check_effects(self, expected_outputs, obsolescence_management):
        self.content.refresh_from_db()
        self.assertEqual(self.content.is_obsolete, expected_outputs["is_obsolete"])
        self.assertEqual(self.content.obsolescence_description, expected_outputs["text"])
        self.assertEqual(obsolescence_management.send.call_count, expected_outputs["call_count"])
