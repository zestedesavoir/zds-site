import datetime
from django.test import TestCase
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.tests.factories import PublishedContentFactory
from zds.utils.misc import contains_utf8mb4
from zds.utils.models import Alert
from zds.utils.context_processor import get_header_notifications


class Misc(TestCase):
    def test_utf8mb4(self):
        self.assertFalse(contains_utf8mb4("abc"))
        self.assertFalse(contains_utf8mb4("abc"))
        self.assertFalse(contains_utf8mb4("abc€"))
        self.assertFalse(contains_utf8mb4("abc€"))
        self.assertTrue(contains_utf8mb4("a🐙tbc€"))
        self.assertTrue(contains_utf8mb4("a🐙tbc€"))

    def test_intervention_filter_for_tribunes(self):
        author = ProfileFactory()
        opinion = PublishedContentFactory(type="OPINION", author_list=[author.user])
        alerter = ProfileFactory()
        staff = StaffProfileFactory()
        alert = Alert()
        alert.scope = "CONTENT"
        alert.author = alerter.user
        alert.content = opinion
        alert.pubdate = datetime.datetime.now()
        alert.text = "Something to say."
        alert.save()
        filter_result = get_header_notifications(staff.user)["alerts"]
        self.assertEqual(1, filter_result["total"])
        self.assertEqual(alert.text, filter_result["list"][0]["text"])
