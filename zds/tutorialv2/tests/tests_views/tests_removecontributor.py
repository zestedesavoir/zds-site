from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import ContentContribution
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ContentContributionRoleFactory, PublishableContentFactory


def create_contribution(role, contributor, content):
    contribution = ContentContribution(contribution_role=role, user=contributor, content=content)
    contribution.save()
    return contribution


@override_for_contents()
class RemoveContributorPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user
        self.contributor = ProfileFactory().user

        # Create a contribution role
        self.role = ContentContributionRoleFactory(title="Contributeur espiègle")

        # Create content
        self.content = PublishableContentFactory(author_list=[self.author])
        self.contribution = create_contribution(self.role, self.contributor, self.content)

        # Get information to be reused in tests
        self.form_url = reverse("content:remove-contributor", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.form_url
        self.content_url = reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.form_data = {"pk_contribution": self.contribution.pk}

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        self.content.type = "TUTORIAL"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_author(self):
        self.client.force_login(self.author)
        self.content.type = "TUTORIAL"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff_tutorial(self):
        self.client.force_login(self.staff)
        self.content.type = "TUTORIAL"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff_article(self):
        self.client.force_login(self.staff)
        self.content.type = "ARTICLE"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff_opinion(self):
        self.client.force_login(self.staff)
        self.content.type = "OPINION"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)


class RemoveContributorWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create entities for the test
        self.author = ProfileFactory().user
        self.contributor = ProfileFactory().user
        self.content = PublishableContentFactory(author_list=[self.author])
        self.role = ContentContributionRoleFactory(title="Validateur")
        self.contribution = create_contribution(self.role, self.contributor, self.content)

        # Get information to be reused in tests
        self.form_url = reverse("content:remove-contributor", kwargs={"pk": self.content.pk})
        self.success_message_fragment = _("Vous avez enlevé ")
        self.error_message_fragment = _("Les contributeurs sélectionnés n'existent pas.")

        # Log in with an authorized user to perform the tests
        self.client.force_login(self.author)

    def check_signal(self, contributors_management, emitted):
        """Assert whether the signal is appropriately emitted."""
        if emitted:
            self.assertEqual(contributors_management.send.call_count, 1)
            self.assertEqual(contributors_management.send.call_args[1]["action"], "remove")
        else:
            self.assertFalse(contributors_management.send.called)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_existing(self, contributors_management):
        response = self.client.post(self.form_url, {"pk_contribution": self.contribution.pk}, follow=True)
        self.assertContains(response, escape(self.success_message_fragment))
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=True)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_empty(self, contributors_management):
        response = self.client.post(self.form_url, {"pk_contribution": ""}, follow=True)
        self.assertContains(response, escape(self.error_message_fragment))
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_invalid(self, contributors_management):
        response = self.client.post(self.form_url, {"pk_contribution": "420"}, follow=True)  # pk must not exist
        self.assertEqual(response.status_code, 404)
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_not_integer(self, contributors_management):
        with self.assertRaises(ValueError):
            self.client.post(self.form_url, {"pk_contribution": "abcd"}, follow=True)
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_no_argument(self, contributors_management):
        response = self.client.post(self.form_url, follow=True)
        self.assertContains(response, escape(self.error_message_fragment))
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_wrong_contribution(self, contributors_management):
        form_url = reverse("content:remove-contributor", kwargs={"pk": 3023})  # pk must not exist
        response = self.client.post(form_url, follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])
        self.check_signal(contributors_management, emitted=False)
