# coding: utf-8

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _

from zds.forum.models import Post
from zds.forum.factories import CategoryFactory, ForumFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.forum.tests.tests_views import create_category, add_topic_in_a_forum
from zds.utils.models import CommentEdit
from zds.utils.templatetags.emarkdown import render_markdown


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PagesMemberTests(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory().user
        log = self.client.login(
            username=self.user1.username,
            password='hostel77')
        self.assertEqual(log, True)

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse('pages-eula'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse('pages-about'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse('pages-contact'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse('pages-association'),
        )

        self.assertEqual(result.status_code, 200)

    def test_subscribe_association(self):
        """
        To test the "subscription to the association" form.
        """
        forum_category = CategoryFactory(position=1)
        forum = ForumFactory(category=forum_category, position_in_category=1)

        # overrides the settings to avoid 404 if forum does not exist
        settings.ZDS_APP['site']['association']['forum_ca_pk'] = forum.pk

        # send form
        long_str = u''
        for i in range(3100):
            long_str += u'A'

        result = self.client.post(
            reverse('pages-assoc-subscribe'),
            {
                'full_name': 'Anne Onyme',
                'email': 'anneonyme@test.com',
                'naissance': '01 janvier 1970',
                'adresse': '42 rue du savoir, appartement 42, 75000 Paris, France',
                'justification': long_str
            },
            follow=False)

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse('pages-cookies'),
        )

        self.assertEqual(result.status_code, 200)


class PagesStaffTests(TestCase):

    def setUp(self):
        self.staff = StaffProfileFactory().user
        log = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(log, True)

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse('pages-eula'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse('pages-about'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse('pages-contact'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse('pages-association'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse('pages-cookies'),
        )

        self.assertEqual(result.status_code, 200)


class PagesGuestTests(TestCase):

    def test_url_home(self):
        """Test: check that home page is alive."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_eula(self):
        """Test: check that eula page is alive."""

        result = self.client.get(
            reverse('pages-eula'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_about(self):
        """Test: check that about page is alive."""

        result = self.client.get(
            reverse('pages-about'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_contact(self):
        """Test: check that contact page is alive."""

        result = self.client.get(
            reverse('pages-contact'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_association(self):
        """Test: check that association page is alive."""

        result = self.client.get(
            reverse('pages-association'),
        )

        self.assertEqual(result.status_code, 200)

    def test_url_cookies(self):
        """Test: check that cookies page is alive."""

        result = self.client.get(
            reverse('pages-cookies'),
        )

        self.assertEqual(result.status_code, 200)

    def test_render_template(self):
        """Test: render_template() works and git_version is in template."""

        result = self.client.get(
            reverse('homepage'),
        )

        self.assertTrue('git_version' in result.context)


class CommentEditsHistoryTests(TestCase):

    def setUp(self):
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, self.user.profile)

        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        data = {
            'text': 'A new post!'
        }
        self.client.post(
            reverse('post-edit') + '?message={}'.format(topic.last_message.pk), data, follow=False)
        self.post = topic.last_message
        self.edit = CommentEdit.objects.latest('date')

    def test_history_with_wrong_pk(self):
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk + 1]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('edit-detail', args=[self.edit.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_history_access(self):
        # Logout and check that the history can't be displayed
        self.client.logout()
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk]))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('edit-detail', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)

        # Login with another user and check that the history can't be displayed
        other_user = ProfileFactory().user
        self.assertTrue(self.client.login(username=other_user.username, password='hostel77'))
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('edit-detail', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)

        # Login as staff and check that the history can be displayed
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('edit-detail', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 200)

        # And finally, check that the post author can see the history
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('edit-detail', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_history_content(self):
        # Login as staff
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))

        # Check that there is a row on the history
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk]))
        self.assertContains(response, _(u'Voir'))
        self.assertIn(self.edit, response.context['edits'])

        # Check that there is a button to delete the edit content
        self.assertContains(response, _(u'Supprimer'))

        # And not when we're logged as author
        self.client.logout()
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        response = self.client.get(reverse('comment-edits-history', args=[self.post.pk]))
        self.assertNotContains(response, _(u'Supprimer'))

    def test_edit_detail(self):
        # Login as staff
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))

        # Check that the original content is displayed
        response = self.client.get(reverse('edit-detail', args=[self.edit.pk]))
        original_text_html, metadata = render_markdown(self.edit.original_text, disable_ping=True)
        self.assertContains(response, original_text_html)

    def test_restore_original_content(self):
        original_edits_count = CommentEdit.objects.count()

        # Test that this option is only available for author and staff
        other_user = ProfileFactory().user
        self.assertTrue(self.client.login(username=other_user.username, password='hostel77'))
        response = self.client.post(reverse('restore-edit', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        response = self.client.post(reverse('restore-edit', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))
        response = self.client.post(reverse('restore-edit', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)

        # Test that a sanctionned user can't do this
        self.user.profile.can_write = False
        self.user.profile.save()
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        response = self.client.post(reverse('restore-edit', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)

        # Test that the text was restored
        self.post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(self.post.text, self.edit.original_text)

        # And that two archives (tests by author and staff) were created
        self.assertEqual(original_edits_count + 2, CommentEdit.objects.count())

    def test_delete_original_content(self):
        # This option should only be available for staff
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))
        response = self.client.post(reverse('delete-edit-content', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))
        response = self.client.post(reverse('delete-edit-content', args=[self.edit.pk]))
        self.assertEqual(response.status_code, 302)

        # Test that the edit content was removed
        self.edit = CommentEdit.objects.get(pk=self.edit.pk)
        self.assertEqual(self.edit.original_text, '')
        self.assertIsNotNone(self.edit.deleted_at)
        self.assertEqual(self.edit.deleted_by, self.staff)
