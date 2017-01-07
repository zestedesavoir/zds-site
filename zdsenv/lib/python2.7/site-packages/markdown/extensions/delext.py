#! /usr/bin/env python

# Inspired by https://github.com/aleray/mdx_del_ins/blob/master/mdx_del_ins.py

from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagPattern

DEL_RE = r"(\~\~)(.+?)(\~\~)"


class DelExtension(Extension):
    """Adds del extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.inlinePatterns.add('del', SimpleTagPattern(DEL_RE, 'del'), '<not_strong')


def makeExtension(*args, **kwargs):
    return DelExtension(*args, **kwargs)
