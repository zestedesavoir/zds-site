# coding: utf-8

from markdown import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import get_template
from django.template import Context
from zds.poll.models import Poll


class PollExtension(Extension):
    def __init__(self, configs):
        super(PollExtension, self).__init__(configs)
        self.config = {}

        for key, value in configs.items():
            self.config[key][0] = value

    def extendMarkdown(self, md, md_globals):
        poll_re = u'^\[\[sondage\{(?P<poll_pk>\d+)\}\]\]'
        md.inlinePatterns.add('polls', PollPattern(poll_re), "<linebreak")


class PollPattern(Pattern):
    def __init__(self, pattern):
        Pattern.__init__(self, pattern)

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
