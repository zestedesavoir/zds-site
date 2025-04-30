from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests.factories import PublishedContentFactory
from zds.tutorialv2.models.database import PotentialObsolete


class ObsoleteViewsTests(TestCase):
    def setUp(self):
        self.user = ProfileFactory().user
        self.staff_user = StaffProfileFactory().user
        self.content = PublishedContentFactory()
        self.content.authors.add(self.user)
        self.client.force_login(self.staff_user)

    @patch("zds.tutorialv2.views.validations_contents.get_bot_account")
    @patch("zds.tutorialv2.views.validations_contents.send_mp")
    def test_mark_obsolete_first_time(self, mock_send_mp, mock_get_bot):
        self.content.obsolete_reason = None
        self.content.save()

        url = reverse("content:mark-obsolete", kwargs={"pk": self.content.pk})
        response = self.client.post(url, {"text": "Outdated section"})

        self.content.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.content.obsolete_reason, "Outdated section")
        mock_send_mp.assert_called()

    @patch("zds.tutorialv2.views.validations_contents.get_bot_account")
    @patch("zds.tutorialv2.views.validations_contents.send_mp")
    def test_mark_obsolete_remove(self, mock_send_mp, mock_get_bot):
        self.content.obsolete_reason = "Old"
        self.content.save()

        url = reverse("content:mark-obsolete", kwargs={"pk": self.content.pk})
        response = self.client.post(url)

        self.content.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.content.obsolete_reason)

    @patch("zds.tutorialv2.views.validations_contents.get_bot_account")
    @patch("zds.tutorialv2.views.validations_contents.send_mp")
    def test_decide_obsolete_mark_true(self, mock_send_mp, mock_get_bot):
        report = PotentialObsolete.objects.create(
            message="Report about outdated info",
            author=self.user,
            publishable_content=self.content,
            status="nouveau",  # Default to "new"
        )
        url = reverse("content:decide-obsolete", kwargs={"pk": report.pk})
        response = self.client.post(url, {"decision_obsolete": "True", "text": "Confirmed obsolete"})

        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.content.refresh_from_db()
        self.assertEqual(report.status, "traite")
        self.assertEqual(self.content.obsolete_reason, "Confirmed obsolete")

    def test_decide_obsolete_mark_false(self):
        report = PotentialObsolete.objects.create(
            message="Another report",
            author=self.user,
            publishable_content=self.content,
            status="nouveau",  # Default to "new"
        )
        url = reverse("content:decide-obsolete", kwargs={"pk": report.pk})
        response = self.client.post(url, {"decision_obsolete": "False"})

        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, "ignore")

    @patch("zds.tutorialv2.views.validations_contents.get_bot_account")
    @patch("zds.tutorialv2.views.validations_contents.send_mp")
    def test_report_obsolete(self, mock_send_mp, mock_get_bot):
        self.content.obsolete_reason = None
        self.content.save()

        url = reverse("content:report-obsolete", kwargs={"pk": self.content.pk})
        response = self.client.post(url, {"text": "Seems outdated"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(PotentialObsolete.objects.filter(publishable_content=self.content).exists())
        mock_send_mp.assert_called()
