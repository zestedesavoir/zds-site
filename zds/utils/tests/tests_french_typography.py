from django.test import TestCase
from django.utils.safestring import mark_safe

from zds.utils.templatetags.french_typography import french_typography


class FrenchTypographyTests(TestCase):
    @staticmethod
    def get_cases():
        return {
            # Narrow non-breaking space: &#8239;
            "semicolon": {"input": " ;", "expected_output": mark_safe("&#8239;;")},
            "question mark": {"input": " ?", "expected_output": mark_safe("&#8239;?")},
            "exclamation mark": {"input": " !", "expected_output": mark_safe("&#8239;!")},
            "percent sign": {"input": " %", "expected_output": mark_safe("&#8239;%")},
            # Non-breaking space: &nbsp;
            "opening double guillemet": {"input": "« ", "expected_output": mark_safe("«&nbsp;")},
            "closing double guillemet": {"input": " »", "expected_output": mark_safe("&nbsp;»")},
            "colon": {"input": " :", "expected_output": mark_safe("&nbsp;:")},
            # Miscellaneous
            "several replacements": {
                "input": "Ô râge, oh ?! des zestes poires !",
                "expected_output": mark_safe("Ô râge, oh&#8239;?! des zestes poires&#8239;!"),
            },
            "no replacement": {"input": "Pulpe Fiction.", "expected_output": "Pulpe Fiction."},
            "empty string": {"input": "", "expected_output": ""},
        }

    def test_french_typography(self):
        test_cases = FrenchTypographyTests.get_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                self.assertEqual(case["expected_output"], french_typography(case["input"]))
