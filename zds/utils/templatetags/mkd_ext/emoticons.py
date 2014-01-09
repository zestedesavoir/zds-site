"""
Emoticon Extension for python-markdown
======================================

Converts defined emoticon symbols to images, with the symbols as their ``alt``
text. Requires python-markdown 1.6+.

Basic usage:

    >>> import markdown
    >>> text = 'Some text with a pre-defined emoticon :p.'
    >>> markdown.markdown(text, ['emoticons'])
    '\\n<p>Some text with a pre-defined emoticon <img src="tongue.gif" alt=":p"/>.\\n</p>\\n\\n\\n'

Simple custom settings:

    >>> md = markdown.markdown(text,
    ...     ['emoticons(BASE_URL=/emoticons/,FILE_EXTENSION=.jpg)']
    ... )
    >>> md
    '\\n<p>Some text with a pre-defined emoticon <img src="/emoticons/tongue.jpg" alt=":p"/>.\\n</p>\\n\\n\\n'

Complex custom settings:

    >>> md = markdown.Markdown(text,
    ...     extensions=['emoticons'],
    ...     extension_configs={'emoticons': [
    ...             ('EMOTICONS', {':p': 'cheeky'}),
    ...             ('BASE_URL', 'http://supoib-emoticons.com/'),
    ...             ('FILE_EXTENSION', '.png'),
    ...         ]})
    >>> md.toString()
    '\\n<p>Some text with a pre-defined emoticon <img src="http://supoib-emoticons.com/cheeky.png" alt=":p"/>.\\n</p>\\n\\n\\n'

"""
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
            [re.escape(emoticon) \
             for emoticon in self.getConfig('EMOTICONS').keys()])
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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
