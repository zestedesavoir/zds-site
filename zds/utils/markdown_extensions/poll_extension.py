# coding: utf-8

from markdown import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import get_template
from django.template import Context
from zds.poll.models import Poll

# !(sondage:2)
POLL_LINK_RE = r'(^|\n)!\(sondage\:(?P<poll_pk>\d+)\)'


class PollExtension(Extension):
    def __init__(self, configs):
        super(PollExtension, self).__init__(configs)
        self.config = {}

        for key, value in configs.items():
            self.config[key][0] = value

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('polls', PollPattern(POLL_LINK_RE), "<linebreak")


class PollPattern(Pattern):
    """ Return a poll element from the given match. """

    def handleMatch(self, m):
        try:
            poll_pk = m.group('poll_pk')
        except IndexError:
            return None

        try:
            poll = Poll.objects.get(pk=int(poll_pk))
        except ObjectDoesNotExist:
            poll = None

        template = get_template('markdown_extensions/poll.html')
        context = Context({"poll": poll})

        el = etree.fromstring(str(template.render(context)))
        return el


def makeExtension(configs=None):
    return PollExtension(configs=configs)
