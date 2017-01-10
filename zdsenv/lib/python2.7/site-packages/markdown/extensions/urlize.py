# Inspired by https://github.com/r0wb0t/markdown-urlize/blob/master/urlize.py

from __future__ import unicode_literals
from markdown.inlinepatterns import Pattern as InlinePattern, sanitize_url, MAIL_RE
from markdown import Extension, util
try:  # pragma: no cover
    from urllib.parse import urlparse
except ImportError:  # pragma: no cover
    from urlparse import urlparse
import re

# Global Vars. Do not catch ending dot
URLIZE_RE = r'(^|(?<=\s))({0})(?=\.?(\s|$))'.format("|".join((
    # mail adress (two lines):
    MAIL_RE,
    # Anything with protocol between < >
    r"<(?:f|ht)tps?://[^>]*>",
    # with protocol : any valid domain match.
    r"((?:f|ht)tps?://)([\da-z\.-]+)\.([a-z\.]{1,5}[a-z])([/\w\.$%&_?#=()'-]*[/\w$%&_?#=()'-])?\/?",
    # without protocol, only somes specified protocols match
    r"((?:f|ht)tps?://)?([\da-z\.-]+)\.(?:com|net|org|fr)([/\w\.$%&_?#=()'-]*[/\w$%&_?#=()'-])?\/?")))


class UrlizePattern(InlinePattern):
    """ Return a link Element given an autolink (`http://example/com`). """

    def __init__(self, *args, **kwargs):
        kwargs["not_in"] = ('link',)
        InlinePattern.__init__(self, *args, **kwargs)

    def handleMatch(self, m):

        url = m.group(3)

        if url.startswith('<'):
            url = url[1:-1]

        text = url
        is_url = re.match(MAIL_RE, url)

        if not is_url:
            url = sanitize_url(url)

        parts = urlparse(url)

        # If no protocol (and not explicit relative link), add one
        if parts[0] == "":
            if is_url:
                url = 'mailto:' + url
            elif not url.startswith("#") and not url.startswith("/"):
                url = 'http://' + url

        el = util.etree.Element("a")
        el.set('href', url)
        el.text = util.AtomicString(text)
        return el


class UrlizeExtension(Extension):
    """ Urlize Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Replace autolink with UrlizePattern """
        md.inlinePatterns['autolink'] = UrlizePattern(URLIZE_RE, md)


def makeExtension(*args, **kwargs):
    return UrlizeExtension(*args, **kwargs)
