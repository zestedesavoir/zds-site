# -*- coding: utf-8 -*-

from django.test import TestCase
from django.template import Context, Template


class EMarkdownTest(TestCase):
    def setUp(self):
        content = u'# Titre 1\n\n## Titre **2**\n\n### Titre 3\n\n> test'
        self.context = Context({'content': content})

    def test_emarkdown(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template('{% load emarkdown %}{{ content | emarkdown}}').render(self.context)

        expected = ('<h3>Titre 1</h3>\n'
                    '<h4>Titre <strong>2</strong></h4>\n'
                    '<h5>Titre 3</h5>\n'
                    '<blockquote>\n'
                    '<p>test</p>\n'
                    '</blockquote>')
        self.assertEqual(tr, expected)

        # Todo: Found a way to force parsing crash or simulate it.

    def test_emarkdown_inline(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template('{% load emarkdown %}{{ content | emarkdown_inline}}').render(self.context)

        expected = ('<p># Titre 1\n\n'
                    '## Titre <strong>2</strong>\n\n'
                    '### Titre 3\n\n'
                    '> test</p>')

        self.assertEqual(tr, expected)

        # Todo: Found a way to force parsing crash or simulate it.

    def test_shift_heading(self):
        tr = Template('{% load emarkdown %}{{ content | shift_heading_1}}').render(self.context)
        self.assertEqual(u'## Titre 1\n\n'
                         '### Titre **2**\n\n'
                         '#### Titre 3\n\n'
                         '&gt; test', tr)

        tr = Template('{% load emarkdown %}{{ content | shift_heading_2}}').render(self.context)
        self.assertEqual(u'### Titre 1\n\n'
                         '#### Titre **2**\n\n'
                         '##### Titre 3\n\n'
                         '&gt; test', tr)

        tr = Template('{% load emarkdown %}{{ content | shift_heading_3}}').render(self.context)
        self.assertEqual(u'#### Titre 1\n\n'
                         '##### Titre **2**\n\n'
                         '###### Titre 3\n\n'
                         '&gt; test', tr)
