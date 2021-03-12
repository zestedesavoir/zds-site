from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Post
from zds.forum.factories import create_category_and_forum, create_topic_in_forum
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.utils.models import CommentEdit
from zds.utils.templatetags.emarkdown import render_markdown


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PagesMemberTests(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        log = self.client.login(username=self.user1.username, password="hostel77")
        self.assertEqual(log, True)

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse("homepage"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse("pages-eula"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse("pages-about"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse("pages-contact"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse("pages-association"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse("pages-cookies"),
        )

        self.assertEqual(result.status_code, 200)


class PagesStaffTests(TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory().user
        log = self.client.login(username=self.staff.username, password="hostel77")
        self.assertEqual(log, True)

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse("homepage"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse("pages-eula"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse("pages-about"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse("pages-contact"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse("pages-association"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse("pages-cookies"),
        )

        self.assertEqual(result.status_code, 200)


class PagesGuestTests(TestCase):
    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse("homepage"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse("pages-eula"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse("pages-about"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse("pages-contact"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse("pages-association"),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse("pages-cookies"),
        )

        self.assertEqual(result.status_code, 200)

    def test_render_template(self):
        """Test: render_template() works and version is in template."""

        result = self.client.get(
            reverse("homepage"),
        )

        self.assertTrue("zds_version" in result.context)


class CommentEditsHistoryTests(TestCase):
    def setUp(self):
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, self.user.profile)

        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        data = {"text": "A new post!"}
        self.client.post(reverse("post-edit") + f"?message={topic.last_message.pk}", data, follow=False)
        self.post = topic.last_message
        self.edit = CommentEdit.objects.latest("date")

    def test_history_with_wrong_pk(self):
        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk + 1]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("edit-detail", args=[self.edit.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_history_access(self):
        # Logout and check that the history can't be displayed
        self.client.logout()
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk]))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("edit-detail", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)

        # Login with another user and check that the history can't be displayed
        other_user = ProfileFactory().user
        self.assertTrue(self.client.login(username=other_user.username, password="hostel77"))
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("edit-detail", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)

        # Login as staff and check that the history can be displayed
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("edit-detail", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 200)

        # And finally, check that the post author can see the history
        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("edit-detail", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_history_content(self):
        # Login as staff
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))

        # Check that there is a row on the history
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk]))
        self.assertContains(response, _("Voir"))
        self.assertIn(self.edit, response.context["edits"])

        # Check that there is a button to delete the edit content
        self.assertContains(response, _("Supprimer"))

        # And not when we're logged as author
        self.client.logout()
        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        response = self.client.get(reverse("comment-edits-history", args=[self.post.pk]))
        self.assertNotContains(response, _("Supprimer"))

    def test_edit_detail(self):
        # Login as staff
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))

        # Check that the original content is displayed
        response = self.client.get(reverse("edit-detail", args=[self.edit.pk]))
        original_text_html, *_ = render_markdown(self.edit.original_text, disable_ping=True)
        self.assertContains(response, original_text_html)

    def test_restore_original_content(self):
        original_edits_count = CommentEdit.objects.count()

        # Test that this option is only available for author and staff
        other_user = ProfileFactory().user
        self.assertTrue(self.client.login(username=other_user.username, password="hostel77"))
        response = self.client.post(reverse("restore-edit", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        response = self.client.post(reverse("restore-edit", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        response = self.client.post(reverse("restore-edit", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)

        # Test that a sanctionned user can't do this
        self.user.profile.can_write = False
        self.user.profile.save()
        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        response = self.client.post(reverse("restore-edit", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)

        # Test that the text was restored
        self.post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(self.post.text, self.edit.original_text)

        # And that two archives (tests by author and staff) were created
        self.assertEqual(original_edits_count + 2, CommentEdit.objects.count())

    def test_delete_original_content(self):
        # This option should only be available for staff
        self.assertTrue(self.client.login(username=self.user.username, password="hostel77"))
        response = self.client.post(reverse("delete-edit-content", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username=self.staff.username, password="hostel77"))
        response = self.client.post(reverse("delete-edit-content", args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)

        # Test that the edit content was removed
        self.edit = CommentEdit.objects.get(pk=self.edit.pk)
        self.assertEqual(self.edit.original_text, "")
        self.assertIsNotNone(self.edit.deleted_at)
        self.assertEqual(self.edit.deleted_by, self.staff)
