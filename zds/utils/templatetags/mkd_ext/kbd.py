#! /usr/bin/env python

import markdown
from markdown.inlinepatterns import SimpleTagPattern

# Small extension to parse ||Touche|| in Kbd html tag (cgabard)

KBD_RE = r"(\|\|)(.+?)(\|\|)"


class KbdExtension(markdown.extensions.Extension):
    """Adds kdb extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.inlinePatterns.add('kbd', SimpleTagPattern(KBD_RE, 'kbd'), '<not_strong')


def makeExtension(configs={}):
    return KbdExtension(configs=dict(configs))

