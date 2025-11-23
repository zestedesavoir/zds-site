from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.forum.tests.factories import TagFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.tags import EditTags, EditTagsForm
from zds.utils.forms import TagValidator
from zds.utils.models import Tag


@override_for_contents()
class EditContentTagsPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-tags", kwargs={"pk": self.content.pk})
        self.form_data = {"tags": "test2, test2"}
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
class EditContentTagsWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user])

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-tags", kwargs={"pk": self.content.pk})
        self.error_messages = EditTagsForm.declared_fields["tags"].error_messages
        self.success_message = EditTags.success_message

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        self.client.force_login(self.author.user)

    def get_test_cases(self):
        special_char_for_slug = "?"
        tag_length_max = Tag._meta.get_field("title").max_length
        tag_too_long = "a" * (tag_length_max + 1)
        tag_utf8mb4 = "😁"
        return {
            "empty_form": {"inputs": {}, "expected_outputs": [self.success_message]},
            "empty_fields": {"inputs": {"tags": ""}, "expected_outputs": [self.success_message]},
            "success_tags": {"inputs": {"tags": "test, test1"}, "expected_outputs": [self.success_message]},
            "stripped_to_empty": {"inputs": {"tags": " "}, "expected_outputs": [self.success_message]},
            "tags_string_too_long": {
                "inputs": {"tags": "a" * (EditTagsForm.declared_fields["tags"].max_length + 1)},
                "expected_outputs": [self.error_messages["max_length"]],
            },
            "invalid_slug_tag": {
                "inputs": {"tags": special_char_for_slug},
                "expected_outputs": [TagValidator.error_empty_slug.format(special_char_for_slug)],
            },
            "tag_too_long": {
                "inputs": {"tags": tag_too_long},
                "expected_outputs": [TagValidator.error_tag_too_long.format(tag_too_long, tag_length_max)],
            },
            "tag_utf8mb4": {
                "inputs": {"tags": tag_utf8mb4},
                "expected_outputs": [TagValidator.error_utf8mb4.format(tag_utf8mb4)],
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
class EditContentTagsFunctionalTests(TutorialTestMixin, TestCase):
    """Test the detailed behavior of the feature, such as updates of the database or repositories."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create tags
        self.tag_0 = TagFactory()
        self.tag_1 = TagFactory()
        self.tag_from_other_content = TagFactory()
        self.tags_name = [self.tag_0.title, self.tag_1.title, self.tag_from_other_content.title]

        # Create contents
        self.content = PublishableContentFactory(author_list=[self.author.user])
        self.other_content = PublishableContentFactory(author_list=[self.author.user])
        self.other_content.tags.add(self.tag_from_other_content)
        self.other_content.save()

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-tags", kwargs={"pk": self.content.pk})

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        self.client.force_login(self.author.user)

    def test_form_function(self):
        """Test many use cases for the form."""
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                with patch("zds.tutorialv2.signals.tags_management") as tags_management:
                    self.enforce_preconditions(case["preconditions"])
                    self.post_form(case["inputs"])
                    self.check_effects(case["expected_outputs"], tags_management)

    def get_test_cases(self):
        """List test cases for the license editing form."""
        new_tag_name = "new_tag_for_sure"
        return {
            "nothing": {
                "preconditions": {"all_tags": self.tags_name, "content_tags": []},
                "inputs": {"tags": ""},
                "expected_outputs": {"all_tags": self.tags_name, "content_tags": [], "call_count": 1},
            },
            "existing_tag": {
                "preconditions": {"all_tags": self.tags_name, "content_tags": []},
                "inputs": {"tags": self.tag_1.title},
                "expected_outputs": {"all_tags": self.tags_name, "content_tags": [self.tag_1.title], "call_count": 1},
            },
            "new_tag": {
                "preconditions": {"all_tags": self.tags_name, "content_tags": []},
                "inputs": {"tags": new_tag_name},
                "expected_outputs": {
                    "all_tags": self.tags_name + [new_tag_name],
                    "content_tags": [new_tag_name],
                    "call_count": 1,
                },
            },
        }

    def enforce_preconditions(self, preconditions):
        """Prepare the test environment to match given preconditions"""
        tags = []
        for t in preconditions["content_tags"]:
            tags.append(Tag.objects.get(title=t))
        self.content.tags.set(tags)
        self.assertEqual(list(self.content.tags.values_list("title")), preconditions["content_tags"])

    def post_form(self, inputs):
        """Post the form with given inputs."""
        form_data = {"tags": inputs["tags"]}
        self.client.post(self.form_url, form_data)

    def check_effects(self, expected_outputs, tags_management):
        """Check the effects of having sent the form."""
        updated_content = PublishableContent.objects.get(pk=self.content.pk)
        content_tags_as_string = [tag.title for tag in updated_content.tags.all()]
        all_tags_as_string = [tag.title for tag in Tag.objects.all()]
        self.assertEqual(content_tags_as_string, expected_outputs["content_tags"])
        self.assertEqual(all_tags_as_string, expected_outputs["all_tags"])
        self.assertEqual(tags_management.send.call_count, expected_outputs["call_count"])
