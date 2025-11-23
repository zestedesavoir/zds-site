from django.test import TestCase

from zds.utils.templatetags.humanize_duration import humanize_duration


class TemplateTagsTest(TestCase):
    def test_main(self):
        test_cases = [
            {"input": -1, "expected": "moins d'une minute"},
            {"input": 0, "expected": "moins d'une minute"},
            {"input": 1, "expected": "1 minute"},
            {"input": 2, "expected": "2 minutes"},
            {"input": 59, "expected": "50 minutes"},
            {"input": 60, "expected": "1 heure"},
            {"input": 72, "expected": "1 heure"},
            {"input": 90, "expected": "1 heure et 30 minutes"},
            {"input": 105, "expected": "1 heure et 45 minutes"},
            {"input": 110, "expected": "1 heure et 45 minutes"},
            {"input": 125, "expected": "2 heures"},
            {"input": 155, "expected": "2 heures et 30 minutes"},
            {"input": "", "expected": "moins d'une minute"},
            {"input": 24 * 60, "expected": "24 heures"},
            {"input": 48 * 60, "expected": "48 heures"},
        ]

        for test_case in test_cases:
            with self.subTest(f"case: {test_case['input']} min"):
                self.assertEqual(humanize_duration(test_case["input"]), test_case["expected"])
