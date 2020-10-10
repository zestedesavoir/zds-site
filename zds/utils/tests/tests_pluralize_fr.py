# Based on default pluralize filter tests :
# https://github.com/django/django/blob/master/tests/template_tests/filter_tests/test_pluralize.py

from decimal import Decimal

from django.test import SimpleTestCase

from zds.utils.templatetags.pluralize_fr import pluralize_fr


class FunctionTests(SimpleTestCase):
    def test_integers(self):
        self.assertEqual(pluralize_fr(1), "")
        self.assertEqual(pluralize_fr(0), "")
        self.assertEqual(pluralize_fr(2), "s")

    def test_floats(self):
        self.assertEqual(pluralize_fr(0.5), "")
        self.assertEqual(pluralize_fr(1.5), "")
        self.assertEqual(pluralize_fr(2.5), "s")

    def test_decimals(self):
        self.assertEqual(pluralize_fr(Decimal(1)), "")
        self.assertEqual(pluralize_fr(Decimal(0)), "")
        self.assertEqual(pluralize_fr(Decimal(2)), "s")

    def test_lists(self):
        self.assertEqual(pluralize_fr([1]), "")
        self.assertEqual(pluralize_fr([]), "")
        self.assertEqual(pluralize_fr([1, 2, 3]), "s")

    def test_suffixes(self):
        self.assertEqual(pluralize_fr(1, "es"), "")
        self.assertEqual(pluralize_fr(0, "es"), "")
        self.assertEqual(pluralize_fr(2, "es"), "es")
        self.assertEqual(pluralize_fr(1, "y,ies"), "y")
        self.assertEqual(pluralize_fr(0, "y,ies"), "y")
        self.assertEqual(pluralize_fr(2, "y,ies"), "ies")
        self.assertEqual(pluralize_fr(0, "y,ies,error"), "")
