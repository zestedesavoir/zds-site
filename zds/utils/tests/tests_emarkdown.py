from collections import namedtuple
from textwrap import dedent

from django.template import Context, Template
from django.test import TestCase

from zds.utils.templatetags.emarkdown import shift_heading


class EMarkdownTest(TestCase):
    def setUp(self):
        self.content = "# Titre 1\n\n## Titre **2**\n\n### Titre 3\n\n> test"
        self.context = Context({"content": self.content})
        self.long_expected = (
            '<h3 id="titre-1">Titre 1<a aria-hidden="true" tabindex="-1" href="#titre-1">'
            '<span class="icon icon-link"></span></a></h3>\n<h4 id="titre-2">'
            'Titre <strong>2</strong><a aria-hidden="true" tabindex="-1" href="#titre-2"><span'
            ' class="icon icon-link"></span></a></h4>\n<h5 id="titre-3">Titre 3'
            '<a aria-hidden="true" tabindex="-1" href="#titre-3"><span class="icon icon-link">'
            "</span></a></h5>\n<blockquote>\n<p>test</p>\n</blockquote>"
        )

    def test_emarkdown(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template("{% load emarkdown %}{{ content | emarkdown}}").render(self.context)

        self.assertEqual(tr, self.long_expected)

        # Todo: Find a way to force parsing crash or simulate it.

    def test_epub_markdown(self):
        DirTuple = namedtuple("DirTuple", ["absolute", "relative"])
        image_directory = DirTuple("/some/absolute/path", "../some/relative/path")

        tr = Template("{% load emarkdown %}{{ content | epub_markdown:image_directory }}").render(
            Context({"content": self.content, "image_directory": image_directory})
        )

        self.assertEqual(tr, self.long_expected)

    def test_emarkdown_inline(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it

        tr = Template("{% load emarkdown %}{{ content | emarkdown_inline}}").render(self.context)

        expected = "<p># Titre 1\n\n" "## Titre <strong>2</strong>\n\n" "### Titre 3\n\n" "> test</p>"

        self.assertEqual(tr, expected)

    def test_emarkdown_inline_with_link(self):
        # The goal is not to test zmarkdown but test that template tag correctly call it
        self.context["content"] = "[zds](zestedesavoir.com)"
        tr = Template("{% load emarkdown %}{{ content | emarkdown_inline}}").render(self.context)

        expected = '<p><a rel="nofollow" href="zestedesavoir.com">zds</a></p>'
        self.assertEqual(tr, expected)

    def test_shift_heading(self):
        tr = Template("{% load emarkdown %}{{ content | shift_heading_1}}").render(self.context)
        self.assertEqual("## Titre 1\n\n" "### Titre **2**\n\n" "#### Titre 3\n\n" "&gt; test", tr)

        tr = Template("{% load emarkdown %}{{ content | shift_heading_2}}").render(self.context)
        self.assertEqual("### Titre 1\n\n" "#### Titre **2**\n\n" "##### Titre 3\n\n" "&gt; test", tr)

        tr = Template("{% load emarkdown %}{{ content | shift_heading_3}}").render(self.context)
        self.assertEqual("#### Titre 1\n\n" "##### Titre **2**\n\n" "###### Titre 3\n\n" "&gt; test", tr)

    def test_special_shift_heading(self):
        sharp_in_code = dedent(
            """
        # title
        ```
        # comment
        ```
        # another title
        """
        )
        result_sharp_in_code = dedent(
            """
        ## title
        ```
        # comment
        ```
        ## another title
        """
        )
        self.assertEqual(shift_heading(sharp_in_code, 1), result_sharp_in_code)

        sharp_in_code_with_antiquotes = dedent(
            """
        # title
        ~~~
        ```
        # comment
        ~~~
        # another title
        """
        )
        result_sharp_in_code_with_antiquotes = dedent(
            """
        ## title
        ~~~
        ```
        # comment
        ~~~
        ## another title
        """
        )
        self.assertEqual(shift_heading(sharp_in_code_with_antiquotes, 1), result_sharp_in_code_with_antiquotes)
