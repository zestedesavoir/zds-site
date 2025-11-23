from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models import CONTENT_TYPE_LIST
from zds.tutorialv2.models.database import ContentContribution
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ContentContributionRoleFactory, PublishableContentFactory
from zds.tutorialv2.views.contributors import ContributionForm


def create_contribution(role, contributor, content):
    contribution = ContentContribution(contribution_role=role, user=contributor, content=content)
    contribution.save()
    return contribution


@override_for_contents()
class AddContributorPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user
        self.contributor = ProfileFactory().user
        settings.ZDS_APP["member"]["bot_account"] = ProfileFactory().user.username

        # Create content
        self.content = PublishableContentFactory(author_list=[self.author])
        self.role = ContentContributionRoleFactory(title="Contributeur espiègle")

        # Get information to be reused in tests
        self.form_url = reverse("content:add-contributor", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.form_url
        self.content_url = reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.form_data = {"username": self.contributor, "contribution_role": self.role.pk}

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

    def test_authenticated_staff(self):
        self.client.force_login(self.staff)
        for type in CONTENT_TYPE_LIST:
            with self.subTest(type):
                self.content.type = type
                self.content.save()
                response = self.client.post(self.form_url, self.form_data)
                self.assertRedirects(response, self.content_url)


class AddContributorWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create entities for the test
        self.author = ProfileFactory().user
        self.contributor = ProfileFactory().user
        self.role = ContentContributionRoleFactory(title="Validateur")
        self.content = PublishableContentFactory(author_list=[self.author])
        settings.ZDS_APP["member"]["bot_account"] = ProfileFactory().user.username

        # Get information to be reused in tests
        self.form_url = reverse("content:add-contributor", kwargs={"pk": self.content.pk})
        self.error_message_author_contributor = _("Un auteur ne peut pas être désigné comme contributeur")
        self.error_message_empty_user = _("Veuillez renseigner l'utilisateur")
        self.comment = "What a mischievious person!"

        # Log in with an authorized user to perform the tests
        self.client.force_login(self.author)

    def check_signal(self, contributors_management, emitted):
        """Assert whether the signal is appropriately emitted."""
        if emitted:
            self.assertEqual(contributors_management.send.call_count, 1)
            self.assertEqual(contributors_management.send.call_args[1]["action"], "add")
        else:
            self.assertFalse(contributors_management.send.called)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_correct(self, contributors_management):
        form_data = {
            "username": self.contributor,
            "contribution_role": self.role.pk,
            "comment": self.comment,
        }
        self.client.post(self.form_url, form_data, follow=True)
        contribution = ContentContribution.objects.filter(
            content=self.content.pk,
            user=self.contributor,
            contribution_role=self.role,
            comment=self.comment,
        ).first()
        self.assertEqual(list(ContentContribution.objects.all()), [contribution])

        self.check_signal(contributors_management, emitted=True)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_empty_user(self, contributors_management):
        form_data = {
            "username": "",
            "contribution_role": self.role.pk,
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(response, escape(ContributionForm.declared_fields["username"].error_messages["required"]))
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_no_user(self, contributors_management):
        form_data = {
            "contribution_role": self.role.pk,
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(response, escape(ContributionForm.declared_fields["username"].error_messages["required"]))
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_invalid_user(self, contributors_management):
        form_data = {
            "username": "this pseudo does not exist",
            "contribution_role": self.role.pk,
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(response, escape(self.error_message_empty_user))
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_author_contributor(self, contributors_management):
        form_data = {
            "username": self.author,
            "contribution_role": self.role.pk,
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(response, escape(self.error_message_author_contributor))
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_empty_role(self, contributors_management):
        form_data = {
            "username": self.contributor,
            "contribution_role": "",
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(
            response, escape(ContributionForm.declared_fields["contribution_role"].error_messages["required"])
        )
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_no_role(self, contributors_management):
        form_data = {
            "username": self.contributor,
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(
            response, escape(ContributionForm.declared_fields["contribution_role"].error_messages["required"])
        )
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)

    @patch("zds.tutorialv2.signals.contributors_management")
    def test_invalid_role(self, contributors_management):
        form_data = {
            "username": self.contributor,
            "contribution_role": 3150,  # must be an invalid pk, integer or not
        }
        response = self.client.post(self.form_url, form_data, follow=True)
        self.assertContains(
            response, escape(ContributionForm.declared_fields["contribution_role"].error_messages["invalid_choice"])
        )
        self.assertEqual(list(ContentContribution.objects.all()), [])
        self.check_signal(contributors_management, emitted=False)
