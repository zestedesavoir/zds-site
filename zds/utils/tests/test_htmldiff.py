from django.test import TestCase

from zds.utils.templatetags.htmldiff import htmldiff


class HtmlDiffTests(TestCase):
    def test_empty(self):
        self.assertEqual(htmldiff(b"essai", b"essai"), "<p>Pas de changements.</p>")

    def test_nominal(self):
        self.assertIn("Agrume", htmldiff(b"Agrume", b""))

    def test_encoding(self):
        # Regression test for issue #4824
        self.assertIn("Étrange caractère", htmldiff("Étrange caractère".encode(), b""))
