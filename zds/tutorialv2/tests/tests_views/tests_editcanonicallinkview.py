from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.canonical import EditCanonicalLinkForm, EditCanonicalLinkView
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.publication_utils import publish_content

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

    def add_canonical_link_url(self, canonical_link_management, url):
        self.client.post(self.form_url, data={"source": url}, follow=True)
        expected = {"source": url, "call_count": 1}
        self.check_effects(expected, canonical_link_management)

    def publish(self, is_major_update):
        published = publish_content(self.content, self.content.load_version(), is_major_update=is_major_update)
        self.content.public_version = published
        self.content.save()

    def get_public_content_url(self):
        url = reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug})
        response = self.client.get(url)
        return response

    def check_effects(self, expected_outputs, canonical_link_management):
        self.content.refresh_from_db()
        self.assertEqual(self.content.source, expected_outputs["source"])
        self.assertEqual(canonical_link_management.send.call_count, expected_outputs["call_count"])

    @patch("zds.tutorialv2.signals.canonical_link_management")
    def test_normal(self, canonical_link_management):
        self.add_canonical_link_url(canonical_link_management=canonical_link_management, url="https://example.com")

    @patch("zds.tutorialv2.signals.canonical_link_management")
    def test_empty(self, canonical_link_management):
        self.add_canonical_link_url(canonical_link_management=canonical_link_management, url="")

    @patch("zds.tutorialv2.signals.canonical_link_management")
    def test_canonical_link_appears_on_published_content(self, canonical_link_management):
        valid_url = "https://example.com/original-link"
        self.add_canonical_link_url(canonical_link_management=canonical_link_management, url=valid_url)

        # publication
        self.publish(is_major_update=True)

        # checks if the canonical link is present on the page
        self.assertContains(self.get_public_content_url(), f'<link rel="canonical" href="{valid_url}"')

    @patch("zds.tutorialv2.signals.canonical_link_management")
    def test_canonical_link_doesnt_appear_without_republished_content(self, canonical_link_management):
        valid_url = "https://example.com/original-link"

        # publication
        self.publish(is_major_update=True)

        response = self.client.get(reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug}))
        # checks if the canonical link is not present on the page
        self.assertNotContains(response, f'<link rel="canonical" href="{valid_url}"')

        # add canonical link
        self.add_canonical_link_url(canonical_link_management=canonical_link_management, url=valid_url)

        # checks if the canonical link is present on the page without publication
        self.assertContains(self.get_public_content_url(), f'<link rel="canonical" href="{valid_url}"')

        # minor publication
        self.publish(is_major_update=False)
        # checks if the canonical link is present on the page after minor publication
        self.assertContains(self.get_public_content_url(), f'<link rel="canonical" href="{valid_url}"')

        # major publication
        self.publish(is_major_update=True)
        # checks if the canonical link is still present on the page after major publication
        self.assertContains(self.get_public_content_url(), f'<link rel="canonical" href="{valid_url}"')
