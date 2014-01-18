# Inspired by https://github.com/sgraber/markdown.subscript/blob/master/subscript.py
# version by cgabard

import markdown

# Global Vars
SUBSCRIPT_RE   = r'(\~)([^\~]*)\2'  
SUPERSCRIPT_RE = r'(\^)([^\^]*)\2' 

class SubSuperscriptPattern(markdown.inlinepatterns.Pattern):
    """ Return a sub or superscript Element"""

    def __init__(self, RE, md, tag):
        markdown.inlinepatterns.Pattern.__init__(self, RE, md)
        self.tag = tag

    def handleMatch(self, m):
        text = m.group(3)
        el = markdown.util.etree.Element(self.tag)
        el.text = markdown.util.AtomicString(text)
        return el

class SubSuperscriptExtension(markdown.Extension):
    """ Subscript and superscript Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Replace subscript with SubscriptPattern """
        md.inlinePatterns['subscript'] = SubSuperscriptPattern(SUBSCRIPT_RE, md, "sub")
        md.inlinePatterns['superscript'] = SubSuperscriptPattern(SUPERSCRIPT_RE, md, "sup")

def makeExtension(configs=None):
    return SubSuperscriptExtension(configs=configs)

