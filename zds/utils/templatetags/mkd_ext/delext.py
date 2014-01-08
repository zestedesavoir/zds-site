#! /usr/bin/env python

# From https://github.com/aleray/mdx_del_ins/blob/master/mdx_del_ins.py
# Patched for remove "ins" support by cgabard.

'''
Del/Ins Extension for Python-Markdown
=====================================

Wraps the inline content with ins/del tags.


Usage
-----

    >>> import markdown
    >>> src = """This is ++added content++ and this is ~~deleted content~~""" 
    >>> html = markdown.markdown(src, ['del_ins'])
    >>> print(html)
    <p>This is <ins>added content</ins> and this is <del>deleted content</del>
    </p>


Dependencies
------------

* [Markdown 2.0+](http://www.freewisdom.org/projects/python-markdown/)


Copyright
---------

2011, 2012 [The active archives contributors](http://activearchives.org/)
All rights reserved.

This software is released under the modified BSD License. 
See LICENSE.md for details.
'''


import markdown
from markdown.inlinepatterns import SimpleTagPattern


DEL_RE = r"(\~\~)(.+?)(\~\~)"


class DelExtension(markdown.extensions.Extension):
    """Adds del extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.inlinePatterns.add('del', SimpleTagPattern(DEL_RE, 'del'), '<not_strong')


def makeExtension(configs={}):
    return DelExtension(configs=dict(configs))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
