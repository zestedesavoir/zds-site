from django.test import TestCase
from django.contrib.auth import get_user_model

from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.models.database import PotentialObsolete, REPORT_STATUS

User = get_user_model()


class PotentialObsoleteModelTests(TestCase):
    def setUp(self):
        # Create a user and two pieces of publishable content
        self.author = ProfileFactory().user
        self.content = PublishableContentFactory()

    def test_create_report_sets_fields_and_defaults(self):
        report = PotentialObsolete.objects.create(
            message="Outdated info", author=self.author, publishable_content=self.content
        )

        # The instance should be saved in the database
        self.assertIsNotNone(report.id)
        # Fields should match arguments
        self.assertEqual(report.message, "Outdated info")
        self.assertEqual(report.author, self.author)
        self.assertEqual(report.publishable_content, self.content)
        # Default status should be 'nouveau'
        self.assertEqual(report.status, "nouveau")
        # report_date should be auto_now_add (exists and is recent)
        self.assertIsNotNone(report.report_date)

    def test_update_report_status_valid(self):
        report = PotentialObsolete.objects.create(
            message="Check this", author=self.author, publishable_content=self.content
        )

        # Choose a valid new status from REPORT_STATUS
        valid_statuses = [code for code, _ in REPORT_STATUS if code != report.status]
        new_status = valid_statuses[0]

        # update_report_status should return 1 (one row updated)
        updated_count = PotentialObsolete.update_report_status(report.id, new_status)
        self.assertEqual(updated_count, 1)

        # And the status in the DB should reflect the change
        report.refresh_from_db()
        self.assertEqual(report.status, new_status)

    def test_update_report_status_invalid_raises(self):
        report = PotentialObsolete.objects.create(
            message="Invalid status test", author=self.author, publishable_content=self.content
        )

        with self.assertRaises(ValueError):
            PotentialObsolete.update_report_status(report.id, "not_a_valid_status")
