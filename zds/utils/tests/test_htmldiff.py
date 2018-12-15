from django.test import TestCase

from zds.utils.templatetags.htmldiff import htmldiff


class HtmlDiffTests(TestCase):

    def test_empty(self):
        self.assertEquals(htmldiff('essai'.encode(), 'essai'.encode()), '<p>Pas de changements.</p>')

    def test_nominal(self):
        self.assertIn('Agrume', htmldiff('Agrume'.encode(), ''.encode()))

    def test_encoding(self):
        # Regression test for issue #4824
        self.assertIn('Étrange&nbsp;caractère', htmldiff('Étrange caractère'.encode(), ''.encode()))
