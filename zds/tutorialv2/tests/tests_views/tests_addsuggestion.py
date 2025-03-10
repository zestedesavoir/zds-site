from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import ContentSuggestion
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory, PublishedContentFactory


@override_for_contents()
class AddSuggestionPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create contents and suggestion
        self.content = PublishableContentFactory(author_list=[self.author])
        self.suggestable_content = PublishedContentFactory()

        # Get information to be reused in tests
        self.form_url = reverse("content:add-suggestion", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.form_url
        self.content_url = reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.form_data = {"options": self.suggestable_content.pk}

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
        self.assertRedirects(response, self.content_url)


class AddSuggestionWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create users
        self.staff = StaffProfileFactory().user
        self.author = ProfileFactory().user

        # Createcontents
        self.content = PublishableContentFactory(author_list=[self.author])
        self.suggestable_content_1 = PublishedContentFactory()
        self.suggestable_content_2 = PublishedContentFactory()
        self.unpublished_content = PublishableContentFactory()

        self.not_picked_opinion = PublishedContentFactory()
        self.not_picked_opinion.type = "OPINION"
        self.not_picked_opinion.save()

        # Get information to be reused in tests
        self.form_url = reverse("content:add-suggestion", kwargs={"pk": self.content.pk})
        self.success_message_fragment = _("a été ajouté aux suggestions")
        self.error_message_fragment_unpublished = _("pas suggérer une publication non publique")
        self.error_message_fragment_already_suggested = _("déjà suggéré pour cette publication")
        self.error_message_fragment_self = _("la publication pour elle-même")
        self.error_messge_fragment_not_picked = _("un billet qui n'a pas été mis en avant")

        # Log in with an authorized user to perform the tests
        self.client.force_login(self.staff)

    def check_signal(self, suggestions_management, emitted, count=1):
        """Assert whether the signal is appropriately emitted."""
        if emitted:
            self.assertEqual(suggestions_management.send.call_count, count)
            self.assertEqual(suggestions_management.send.call_args[1]["action"], "add")
        else:
            self.assertFalse(suggestions_management.send.called)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_published_simple(self, suggestions_management):
        response = self.client.post(self.form_url, {"options": self.suggestable_content_1.pk}, follow=True)
        self.assertContains(response, escape(self.success_message_fragment))
        suggestion = ContentSuggestion.objects.get(publication=self.content, suggestion=self.suggestable_content_1)
        self.assertEqual(list(ContentSuggestion.objects.all()), [suggestion])
        self.check_signal(suggestions_management, emitted=True)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_published_multiple(self, suggestions_management):
        response = self.client.post(
            self.form_url, {"options": [self.suggestable_content_1.pk, self.suggestable_content_2.pk]}, follow=True
        )
        self.assertContains(response, escape(self.success_message_fragment))
        suggestion_1 = ContentSuggestion.objects.get(publication=self.content, suggestion=self.suggestable_content_1)
        suggestion_2 = ContentSuggestion.objects.get(publication=self.content, suggestion=self.suggestable_content_2)
        self.assertEqual(list(ContentSuggestion.objects.all()), [suggestion_1, suggestion_2])
        self.check_signal(suggestions_management, emitted=True, count=2)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_already_suggested(self, suggestions_management):
        suggestion = ContentSuggestion(publication=self.content, suggestion=self.suggestable_content_1)
        suggestion.save()
        response = self.client.post(self.form_url, {"options": self.suggestable_content_1.pk}, follow=True)
        self.assertContains(response, escape(self.error_message_fragment_already_suggested))
        self.assertEqual(list(ContentSuggestion.objects.all()), [suggestion])
        self.check_signal(suggestions_management, emitted=False)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_self(self, suggestions_management):
        response = self.client.post(self.form_url, {"options": self.content.pk}, follow=True)
        self.assertContains(response, escape(self.error_message_fragment_self))
        self.assertQuerysetEqual(ContentSuggestion.objects.all(), [])
        self.check_signal(suggestions_management, emitted=False)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_not_picked_opinion(self, suggestions_management):
        response = self.client.post(self.form_url, {"options": self.not_picked_opinion.pk}, follow=True)
        self.assertContains(response, escape(self.error_messge_fragment_not_picked))
        self.assertQuerysetEqual(ContentSuggestion.objects.all(), [])
        self.check_signal(suggestions_management, emitted=False)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_unpublished(self, suggestions_management):
        response = self.client.post(self.form_url, {"options": self.unpublished_content.pk}, follow=True)
        self.assertContains(response, escape(self.error_message_fragment_unpublished))
        self.assertQuerysetEqual(ContentSuggestion.objects.all(), [])
        self.check_signal(suggestions_management, emitted=False)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_invalid(self, suggestions_management):
        response = self.client.post(self.form_url, {"options": "420"}, follow=True)  # pk must not exist
        self.assertEqual(response.status_code, 404)
        self.check_signal(suggestions_management, emitted=False)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_not_integer(self, suggestions_management):
        with self.assertRaises(ValueError):
            self.client.post(self.form_url, {"options": "abcd"}, follow=True)
        self.check_signal(suggestions_management, emitted=False)

    @patch("zds.tutorialv2.signals.suggestions_management")
    def test_empty(self, suggestions_management):
        with self.assertRaises(ValueError):
            self.client.post(self.form_url, {"options": ""}, follow=True)
        self.check_signal(suggestions_management, emitted=False)
