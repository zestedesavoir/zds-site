from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests.factories import LabelFactory, PublishableContentFactory, PublishedContentFactory


class EditLabelsPermissionTests(TestCase):
    def setUp(self):
        self.user = ProfileFactory().user
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.content = PublishableContentFactory()
        self.content.authors.add(self.author)
        self.good_url = reverse("content:edit-labels", kwargs={"pk": self.content.pk})
        self.bad_url = reverse("content:edit-labels", kwargs={"pk": 42})
        self.content_url = reverse("content:view", kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.success_url = self.content_url

    def test_display(self):
        """We shall display the form only for staff, not for authors."""
        fragment = _("Modifier les labels")

        self.client.force_login(self.author)
        response = self.client.get(self.content_url)
        self.assertNotContains(response, fragment)

        self.client.force_login(self.staff)
        response = self.client.get(self.content_url)
        self.assertContains(response, fragment)

    def test_get_method(self):
        """
        GET is forbidden, since the view processes the form but do not display anything.
        Actually, all methods except POST are forbidden, but the test is good enough as is.
        """
        self.client.force_login(self.staff)
        response = self.client.get(self.good_url)
        self.assertEqual(response.status_code, 405)

    def test_unauthenticated_not_existing_pk(self):
        """Invalid pks in URL"""
        self.client.logout()
        response = self.client.post(self.bad_url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_redirected(self):
        """As login is required, unauthenticated users shall be redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.good_url)
        self.login_url = f"{reverse('member-login')}?next={self.good_url}"
        self.assertRedirects(response, self.login_url)

    def test_simple_user_forbidden(self):
        """Simple users shall not be able to access to the view."""
        self.client.force_login(self.user)
        response = self.client.post(self.good_url)
        self.assertEqual(response.status_code, 403)

    def test_staff_authorized(self):
        """Staff shall have access to the view."""
        self.client.force_login(self.staff)
        response = self.client.post(self.good_url)
        self.assertRedirects(response, self.success_url)


class EditLabelsFunctionalTests(TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory().user
        self.content = PublishableContentFactory()
        self.content = PublishableContentFactory()
        self.url = reverse("content:edit-labels", kwargs={"pk": self.content.pk})
        self.labels = [LabelFactory() for _ in range(3)]

    @patch("zds.tutorialv2.signals.labels_management")
    def test_labels_updated(self, labels_management):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {"labels": [label.pk for label in self.labels]}, follow=True)
        self.assertEqual(list(self.content.labels.all()), self.labels)
        self.assertContains(response, "alert-box success")
        self.assertEqual(labels_management.send.call_count, 1)

    @patch("zds.tutorialv2.signals.labels_management")
    def test_invalid_parameters(self, labels_management):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {"labels": [42]}, follow=True)
        self.assertEqual(list(self.content.labels.all()), [])
        self.assertContains(response, "alert-box alert")
        self.assertFalse(labels_management.send.called)


class AssignLabelsTestCase(TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory().user
        self.content_with_label = PublishedContentFactory()
        self.content_without_label = PublishedContentFactory()
        self.url = reverse("content:edit-labels", kwargs={"pk": self.content_with_label.pk})
        self.label = LabelFactory()

    def test_add_label(self):
        self.client.force_login(self.staff)
        self.client.post(self.url, {"labels": [self.label.pk]}, follow=True)
        self.assertIn(self.label, self.content_with_label.labels.all())
        self.assertNotIn(self.label, self.content_without_label.labels.all())

    def test_remove_label(self):
        self.client.force_login(self.staff)
        self.content_with_label.labels.add(self.label)
        self.client.post(self.url, {"labels": []}, follow=True)
        self.assertNotIn(self.label, self.content_with_label.labels.all())
        self.assertNotIn(self.label, self.content_without_label.labels.all())
