from django.test import TestCase
from zds.utils.templatetags.minute_to_duration import minute_to_duration


class TemplateTagsTest(TestCase):
    def test_main(self):
        self.assertEqual(minute_to_duration(0), '')
        self.assertEqual(minute_to_duration(-1), '')
        self.assertEqual(
            minute_to_duration(1),
            '1 minute'
        )
        self.assertEqual(
            minute_to_duration(2),
            '2 minutes'
        )
        self.assertEqual(
            minute_to_duration(59),
            '1 heure'
        )
        self.assertEqual(
            minute_to_duration(60),
            '1 heure'
        )
        self.assertEqual(
            minute_to_duration(72),
            '1 heure'
        )
        self.assertEqual(
            minute_to_duration(90),
            '1 heure et 30 minutes'
        )
        self.assertEqual(
            minute_to_duration(105),
            '1 heure et 45 minutes'
        )
        self.assertEqual(
            minute_to_duration(110),
            '1 heure et 45 minutes'
        )
