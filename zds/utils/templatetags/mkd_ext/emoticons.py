# Emoticon extension for python-markdown
# Original version :
# https://gist.github.com/insin/815656/raw/a68516f1ffc03df465730b3ddef6de0a11b7e9a5/mdx_emoticons.py
#
# Patched by cgabard for supporting newer python-markdown version and extend for support multi-extensions

import re
import markdown
from markdown.inlinepatterns import Pattern
from markdown.util import etree

class EmoticonExtension(markdown.Extension):
    def __init__ (self, configs):
        self.config = {
            'EMOTICONS': [{
                ":)" : "test.png",
                }, 'A mapping from emoticon symbols to image names.'],
            }

        for key, value in configs.iteritems() :
            self.config[key][0] = value

    def extendMarkdown(self, md, md_globals):
        self.md = md
        EMOTICON_RE = '(?P<emoticon>%s)' % '|'.join(
            [re.escape(emoticon) for emoticon in self.getConfig('EMOTICONS').keys()])
        md.inlinePatterns.add('emoticons', EmoticonPattern(EMOTICON_RE, self),">not_strong")

class EmoticonPattern(Pattern):
    def __init__ (self, pattern, emoticons):
        Pattern.__init__(self, pattern)
        self.emoticons = emoticons

    def handleMatch(self, m):
        emoticon = m.group('emoticon')
        el = etree.Element('img')
        el.set('src', '%s' % (self.emoticons.getConfig('EMOTICONS')[emoticon],))
        el.set('alt', emoticon)
        return el

def makeExtension(configs=None) :
    return EmoticonExtension(configs=configs)

