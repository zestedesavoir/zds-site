from django.test import TestCase
from django.template import Context, Template


class EMarkdownTest(TestCase):
    def setUp(self):
        content = '# Titre 1\n\n## Titre **2**\n\n### Titre 3\n\n> test'
        self.context = Context({'content': content})

    def test_emarkdown(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template('{% load emarkdown %}{{ content | emarkdown}}').render(self.context)

        expected = (
            '<h3 id="titre-1">Titre 1<a aria-hidden="true" href="#titre-1">'
            '<span class="icon icon-link"></span></a></h3>\n<h4 id="titre-2">'
            'Titre <strong>2</strong><a aria-hidden="true" href="#titre-2"><span'
            ' class="icon icon-link"></span></a></h4>\n<h5 id="titre-3">Titre 3'
            '<a aria-hidden="true" href="#titre-3"><span class="icon icon-link">'
            '</span></a></h5>\n<blockquote>\n<p>test</p>\n</blockquote>'
        )
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
        self.assertEqual('## Titre 1\n\n'
                         '### Titre **2**\n\n'
                         '#### Titre 3\n\n'
                         '&gt; test', tr)

        tr = Template('{% load emarkdown %}{{ content | shift_heading_2}}').render(self.context)
        self.assertEqual('### Titre 1\n\n'
                         '#### Titre **2**\n\n'
                         '##### Titre 3\n\n'
                         '&gt; test', tr)

        tr = Template('{% load emarkdown %}{{ content | shift_heading_3}}').render(self.context)
        self.assertEqual('#### Titre 1\n\n'
                         '##### Titre **2**\n\n'
                         '###### Titre 3\n\n'
                         '&gt; test', tr)
