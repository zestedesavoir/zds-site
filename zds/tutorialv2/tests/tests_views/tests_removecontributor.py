from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory
from zds.tutorialv2.models.database import ContentContribution, ContentContributionRole
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents


def create_contribution(role, contributor, content):
    contribution = ContentContribution(contribution_role=role, user=contributor, content=content)
    contribution.save()
    return contribution


def create_role(title):
    role = ContentContributionRole(title=title)
    role.save()
    return role


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
        self.role = create_role("Validateur")

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
        self.assertEqual(response.status_code, 403)


class RemoveContributorWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create entities for the test
        self.author = ProfileFactory().user
        self.contributor = ProfileFactory().user
        self.role = create_role("Validateur")
        self.content = PublishableContentFactory(author_list=[self.author])
        self.contribution = create_contribution(self.role, self.contributor, self.content)

        # Get information to be reused in tests
        self.form_url = reverse("content:remove-contributor", kwargs={"pk": self.content.pk})
        self.success_message_fragment = _("Vous avez enlevé ")
        self.error_message_fragment = _("Les contributeurs sélectionnés n'existent pas.")

        # Log in with an authorized user to perform the tests
        self.client.force_login(self.author)

    def test_existing(self):
        response = self.client.post(self.form_url, {"pk_contribution": self.contribution.pk}, follow=True)
        self.assertContains(response, escape(self.success_message_fragment))
        self.assertEqual(list(ContentContribution.objects.all()), [])

    def test_empty(self):
        response = self.client.post(self.form_url, {"pk_contribution": ""}, follow=True)
        self.assertContains(response, escape(self.error_message_fragment))
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])

    def test_invalid(self):
        response = self.client.post(self.form_url, {"pk_contribution": "420"}, follow=True)  # pk must not exist
        self.assertEqual(response.status_code, 404)
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])

    def test_not_integer(self):
        with self.assertRaises(ValueError):
            self.client.post(self.form_url, {"pk_contribution": "abcd"}, follow=True)
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])

    def test_no_argument(self):
        response = self.client.post(self.form_url, follow=True)
        self.assertContains(response, escape(self.error_message_fragment))
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])

    def test_wrong_contribution(self):
        form_url = reverse("content:remove-contributor", kwargs={"pk": 3023})  # pk must not exist
        response = self.client.post(form_url, follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(list(ContentContribution.objects.all()), [self.contribution])
