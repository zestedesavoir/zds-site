from django.test import TestCase
from zds.utils.templatetags.non_breaking_space import non_breaking_space
from django.utils.safestring import mark_safe


class ReplaceNonBreakingSpace(TestCase):

    @staticmethod
    def get_cases():
        return {
            # Narrow non-breaking space: &#8239;
            'point-virgule':
                {'input': ' ;',
                 'expected_output': mark_safe('&#8239;;')},
            'point d\'interrogation':
                {'input': ' ?',
                 'expected_output': mark_safe('&#8239;?')},
            'point d\'exclamation':
                {'input': ' !',
                 'expected_output': mark_safe('&#8239;!')},
            'pourcent':
                {'input': ' %',
                 'expected_output': mark_safe('&#8239;%')},
            # Non-breaking space: &nbsp;
            'guillemet français ouvrant':
                {'input': '« ',
                 'expected_output': mark_safe('«&nbsp;')},
            'guillemet français fermant':
                {'input': ' »',
                 'expected_output': mark_safe('&nbsp;»')},
            'deux-points':
                {'input': ' :',
                 'expected_output': mark_safe('&nbsp;:')}
        }

    def test_non_breaking_space(self):
        test_cases = ReplaceNonBreakingSpace.get_cases()
        for case_name, case in test_cases.items():
                with self.subTest(msg=case_name):
                    self.assertEqual(case['expected_output'], non_breaking_space(case['input']))
