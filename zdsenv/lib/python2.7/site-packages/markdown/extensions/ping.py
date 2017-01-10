import markdown
from markdown.inlinepatterns import Pattern

PING_RE = (r'(?<![^\s])'  # Check that there isn't any space before the ping
           r'@(?:'
           r'([-_\d\w]+)'  # For @ping
           r'|'
           r'\['  # For @[ping long]
           r'([^\[\]\n]+)'  # Match everything excepted [, ] and \n
           r'\]'
           r')')


class PingPattern(Pattern):
    def __init__(self, md, ping_url):
        self.ping_url = ping_url
        Pattern.__init__(self, PING_RE, md)

    def handleMatch(self, m):
        name = m.group(2) if m.group(2) is not None else m.group(3)
        if name is None:    # pragma: no cover
            return None
        url = self.ping_url(name)
        if url is None:
            return None

        dnode = markdown.util.etree.Element('a')

        dnode.set('class', 'ping')
        dnode.set('href', url)
        dnode.text = markdown.util.AtomicString('@{}'.format(name))
        self.markdown.metadata["ping"].add(name)
        return dnode


class PingExtension(markdown.extensions.Extension):
    """Adds ping extension to Markdown class."""

    def __init__(self, *args, **kwargs):
        self.config = {
            "ping_url": [lambda _: None,
                         'Function that should return an url if it is a valid pingeable name else None']}
        super(PingExtension, self).__init__(*args, **kwargs)

    def reset(self):
        self.md.metadata["ping"] = set()

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.inlinePatterns.add('a', PingPattern(md, self.getConfig('ping_url')), '<not_strong')
        self.md = md
        self.reset()
        md.registerExtension(self)
