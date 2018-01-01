from django.test import TestCase
from django.template import Context, Template


class EMarkdownTest(TestCase):
    def setUp(self):
        content = '# Titre 1\n\n## Titre **2**\n\n### Titre 3\n\n> test'
        self.context = Context({'content': content})

    def test_emarkdown(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template('{% load emarkdown %}{{ content | emarkdown}}').render(self.context)

        self.assertEqual('<h3>Titre 1</h3>\n'
                         '<h4>Titre <strong>2</strong></h4>\n'
                         '<h5>Titre 3</h5>\n'
                         '<blockquote>\n'
                         '<p>test</p>\n'
                         '</blockquote>', tr)

        # Todo: Found a way to force parsing crash or simulate it.

    def test_emarkdown_inline(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template('{% load emarkdown %}{{ content | emarkdown_inline}}').render(self.context)

        self.assertEqual('<p># Titre 1\n\n'
                         '## Titre <strong>2</strong>\n\n'
                         '### Titre 3\n\n'
                         '&gt; test\n'
                         '</p>', tr)

        # Todo: Found a way to force parsing crash or simulate it.

    def test_decale_header(self):
        tr = Template('{% load emarkdown %}{{ content | decale_header_1}}').render(self.context)
        self.assertEqual('## Titre 1\n\n'
                         '### Titre **2**\n\n'
                         '#### Titre 3\n\n'
                         '&gt; test', tr)

        tr = Template('{% load emarkdown %}{{ content | decale_header_2}}').render(self.context)
        self.assertEqual('### Titre 1\n\n'
                         '#### Titre **2**\n\n'
                         '##### Titre 3\n\n'
                         '&gt; test', tr)

        tr = Template('{% load emarkdown %}{{ content | decale_header_3}}').render(self.context)
        self.assertEqual('#### Titre 1\n\n'
                         '##### Titre **2**\n\n'
                         '###### Titre 3\n\n'
                         '&gt; test', tr)
