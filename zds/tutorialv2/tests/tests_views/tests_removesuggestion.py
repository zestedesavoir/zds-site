from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory
from zds.tutorialv2.forms import RemoveSuggestionForm
from zds.tutorialv2.models.database import ContentSuggestion
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.views.editorialization import RemoveSuggestion


@override_for_contents()
class RemoveSuggestionPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user
        self.other = ProfileFactory().user

        # Create contents and suggestion
        self.content = PublishableContentFactory(author_list=[self.author])
        self.suggested_content = PublishableContentFactory()
        self.suggestion = ContentSuggestion(publication=self.content, suggestion=self.suggested_content)
        self.suggestion.save()

        # Get information to be reused in tests
        self.form_url = reverse("content:remove-suggestion", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.form_url
        self.content_url = reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.form_data = {"pk_suggestion": self.suggestion.pk}

    def test_not_authenticated(self):
        self.client.logout()
        self.content.type = "TUTORIAL"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_outsider(self):
        self.client.force_login(self.outsider)
        self.content.type = "TUTORIAL"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_author(self):
        # TODO: this behavior is actually wrong, it should be only authorized for staff.
        self.client.force_login(self.author)
        self.content.type = "TUTORIAL"
        self.content.save()
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)

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


class RemoveSuggestionWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create users
        self.staff = StaffProfileFactory().user
        self.author = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])
        self.suggested_content_1 = PublishableContentFactory()
        self.suggested_content_2 = PublishableContentFactory()
        self.suggestion_1 = ContentSuggestion(publication=self.content, suggestion=self.suggested_content_1)
        self.suggestion_1.save()
        self.suggestion_2 = ContentSuggestion(publication=self.content, suggestion=self.suggested_content_2)
        self.suggestion_2.save()

        # Get information to be reused in tests
        self.form_url = reverse("content:remove-suggestion", kwargs={"pk": self.content.pk})
        self.success_message_fragment = _("Vous avez enlevé")
        self.error_messages = RemoveSuggestionForm.declared_fields["pk_suggestion"].error_messages
        print(self.error_messages)
        # Log in with an authorized user to perform the tests
        self.client.force_login(self.staff)

    def test_existing(self):
        response = self.client.post(self.form_url, {"pk_suggestion": self.suggestion_1.pk}, follow=True)
        # Check that we display correct message
        self.assertContains(response, escape(self.success_message_fragment))
        # Check update of database
        with self.assertRaises(ContentSuggestion.DoesNotExist):
            ContentSuggestion.objects.get(pk=self.suggestion_1.pk)
        ContentSuggestion.objects.get(pk=self.suggestion_2.pk)  # succeeds

    def test_empty(self):
        response = self.client.post(self.form_url, {"pk_suggestion": ""}, follow=True)
        self.assertContains(response, escape(self.error_messages["required"]))

    def test_invalid(self):
        response = self.client.post(self.form_url, {"pk_suggestion": "420"}, follow=True)  # pk must not exist
        self.assertContains(response, escape(self.error_messages["does_not_exist"]))

    def test_not_integer(self):
        response = self.client.post(self.form_url, {"pk_suggestion": "abcd"}, follow=True)
        self.assertContains(response, escape(self.error_messages["invalid"]))
