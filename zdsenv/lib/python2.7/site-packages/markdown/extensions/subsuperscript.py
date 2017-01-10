# Inspired by https://github.com/sgraber/markdown.subscript/blob/master/subscript.py

from markdown import inlinepatterns, Extension, util

# Global Vars
SUBSCRIPT_RE = r'(\~)(.+?)(\~)'
SUPERSCRIPT_RE = r'(\^)(.+?)(\^)'


class SubSuperscriptPattern(inlinepatterns.Pattern):
    """ Return a sub or superscript Element"""

    def __init__(self, RE, md, tag):
        inlinepatterns.Pattern.__init__(self, RE, md)
        self.tag = tag

    def handleMatch(self, m):
        text = m.group(3)
        el = util.etree.Element(self.tag)
        el.text = util.AtomicString(text)
        return el


class SubSuperscriptExtension(Extension):
    """ Subscript and superscript Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Replace subscript with SubscriptPattern """
        md.inlinePatterns['subscript'] = SubSuperscriptPattern(SUBSCRIPT_RE, md, "sub")
        md.inlinePatterns['superscript'] = SubSuperscriptPattern(SUPERSCRIPT_RE, md, "sup")
        md.ESCAPED_CHARS.extend(['~', '^'])


def makeExtension(*args, **kwargs):
    return SubSuperscriptExtension(*args, **kwargs)
