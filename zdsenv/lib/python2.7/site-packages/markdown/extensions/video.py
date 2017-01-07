#!/usr/bin/env python

import markdown
from markdown.util import etree
from markdown.blockprocessors import BlockProcessor
import re


class VideoExtension(markdown.Extension):
    def __init__(self, js_support=False, **kwargs):
        markdown.Extension.__init__(self)

        self.config = {
            'dailymotion_width': ['480', 'Width for Dailymotion videos'],
            'dailymotion_height': ['270', 'Height for Dailymotion videos'],
            'vimeo_width': ['500', 'Width for Vimeo videos'],
            'vimeo_height': ['281', 'Height for Vimeo videos'],
            'yahoo_width': ['624', 'Width for Yahoo! videos'],
            'yahoo_height': ['351', 'Height for Yahoo! videos'],
            'youtube_width': ['560', 'Width for Youtube videos'],
            'youtube_height': ['315', 'Height for Youtube videos'],
            'ina_width': ['620', 'Width for INA videos'],
            'ina_height': ['349', 'Height for INA videos'],
            'jsfiddle': [False, ''],
            'jsfiddle_width': ['560', 'Width for jsfiddle'],
            'jsfiddle_height': ['560', 'Height for jsfiddle'],
        }

        self.config['youtube_short_width'] = self.config['youtube_width']
        self.config['youtube_short_height'] = self.config['youtube_height']

        # Override defaults with user settings
        for key, value in kwargs.items():
            self.setConfig(key, value)

        if js_support:
            self.setConfig("jsfiddle", True)

    def add_inline(self, md, name, klass, pat):
        RE = r'(^|\n)!\(' + pat + r'\)'
        md.parser.blockprocessors.add("video-" + name,
                                      klass(md, RE,
                                            self.config["{}_width".format(name)][0],
                                            self.config["{}_height".format(name)][0]),
                                      ">reference")

    def extendMarkdown(self, md, md_globals):
        self.add_inline(md, 'dailymotion', Dailymotion,
                        r'https?://www\.dailymotion\.com/video/(?P<dailymotionid>[a-z0-9]+)(_[\w\-]*)?')
        self.add_inline(md, 'vimeo', Vimeo,
                        r'https?://(www.|)vimeo\.com/(?P<vimeoid>\d+)\S*')
        self.add_inline(md, 'yahoo', Yahoo,
                        r'https?://screen\.yahoo\.com/.+/?')
        self.add_inline(md, 'youtube', Youtube,
                        r'https?://(www\.)?youtube\.com/watch\?\S*v=(?P<youtubeid>\S[^&/]+)'
                        r'(?P<channel>&ab_channel=[\w%]+)?')
        self.add_inline(md, 'youtube_short', Youtube,
                        r'https?://youtu\.be/(?P<youtubeid>\S[^?&/]+)?')
        self.add_inline(md, 'ina', Ina,
                        r'https?://www\.ina\.fr/video/(?P<inaid>[A-Z0-9]+)/([\w\-]*)\.html')
        if self.config["jsfiddle"][0]:
            self.add_inline(md, 'jsfiddle', JsFiddle,
                            r'https?://(www.|)jsfiddle\.net(/(?P<jsfiddleuser>\w+))?/'
                            r'(?P<jsfiddleid>\w+)(/(?P<jsfiddlerev>[0-9]+)|)/?')


class VideoBProcessor(BlockProcessor):
    def __init__(self, md, patt, width, height):
        BlockProcessor.__init__(self, md.parser)
        self.md = md
        self.width = width
        self.height = height
        self.RE = re.compile(patt)

    def test(self, parent, block):
        return bool(self.RE.search(block))

    def run(self, parent, blocks):
        m = self.RE.search(blocks[0])

        el = self.handle_match(m)
        if el is None:
            return False

        block = blocks.pop(0)
        before = block[:m.start()]
        after = block[m.end():]

        if before:  # pragma: no cover
            # This should never occur because regex require that the expression is starting the block.
            # Do not raise an exception because exception should never be generated.
            self.md.parser.parseBlocks(parent, [before])

        parent.append(el)

        if after:
            blocks.insert(0, after)

    @staticmethod
    def extract_url(_):  # pragma: no cover
        # Should be overridden in sub-class
        return ""

    def handle_match(self, m):
        url = self.extract_url(m)
        if url is None:
            return None
        return self.render_iframe(url, self.width, self.height)

    @staticmethod
    def render_iframe(url, width, height):
        iframe = etree.Element('iframe')
        iframe.set('width', width)
        iframe.set('height', height)
        iframe.set('src', url)
        iframe.set('allowfullscreen', 'true')
        iframe.set('frameborder', '0')
        return iframe


class Dailymotion(VideoBProcessor):
    @staticmethod
    def extract_url(m):
        return 'https://www.dailymotion.com/embed/video/%s' % m.group('dailymotionid')


class Vimeo(VideoBProcessor):
    @staticmethod
    def extract_url(m):
        return 'https://player.vimeo.com/video/%s' % m.group('vimeoid')


class Yahoo(VideoBProcessor):
    @staticmethod
    def extract_url(m):
        return m.string + '?format=embed&player_autoplay=false'


class Youtube(VideoBProcessor):
    @staticmethod
    def extract_url(m):
        return 'https://www.youtube.com/embed/%s' % m.group('youtubeid')


class Ina(VideoBProcessor):
    @staticmethod
    def extract_url(m):
        return 'http://player.ina.fr/player/embed/%s/1/1b0bd203fbcd702f9bc9b10ac3d0fc21/560/315/1/148db8' % m.group(
            'inaid')


class JsFiddle(VideoBProcessor):
    @staticmethod
    def extract_url(m):
        fields = (m.group('jsfiddleuser'), m.group('jsfiddleid'), m.group('jsfiddlerev'))
        if fields[0] is not None and fields[2] is None:
            # Only two part, revision could be in id pattern
            try:
                int(fields[1])
                # It is a revision !
                fields = (None, fields[0], fields[1])
            except ValueError:
                pass
        if fields[0] is not None and fields[1] is not None and fields[2] is None:
            # Base version link, should not be allowed because content can be changed externally
            return None
        base = "https://jsfiddle.net/{}/embedded/result,js,html,css/"
        return base.format("/".join([t for t in fields if t is not None]))


def makeExtension(*args, **kwargs):
    return VideoExtension(*args, **kwargs)
