#!/usr/bin/env python

import markdown
from markdown.util import etree
from markdown.blockprocessors import BlockProcessor
import re

class VideoExtension(markdown.Extension):
    def __init__(self, configs={}):
        self.config = {
            'dailymotion_width': ['480', 'Width for Dailymotion videos'],
            'dailymotion_height': ['270', 'Height for Dailymotion videos'],
            'metacafe_width': ['440', 'Width for Metacafe videos'],
            'metacafe_height': ['248', 'Height for Metacafe videos'],
            'veoh_width': ['410', 'Width for Veoh videos'],
            'veoh_height': ['341', 'Height for Veoh videos'],
            'vimeo_width': ['500', 'Width for Vimeo videos'],
            'vimeo_height': ['281', 'Height for Vimeo videos'],
            'yahoo_width': ['624', 'Width for Yahoo! videos'],
            'yahoo_height': ['351', 'Height for Yahoo! videos'],
            'youtube_width': ['560', 'Width for Youtube videos'],
            'youtube_height': ['315', 'Height for Youtube videos'],
        }

        # Override defaults with user settings
        for key, value in configs:
            self.setConfig(key, value)

    def add_inline(self, md, name, klass, pat):
        RE = r'(^|\n)!\(' + pat + r'\)'
        md.parser.blockprocessors.add("video-"+name, VideoBProcessor(md, name, klass, RE, self.config), "_begin")

    def extendMarkdown(self, md, md_globals):
        self.add_inline(md, 'dailymotion', Dailymotion,
            r'https?://www\.dailymotion\.com/video/(?P<dailymotionid>[a-z0-9]+)(_[\w\-]*)?')
        self.add_inline(md, 'metacafe', Metacafe,
            r'http://www\.metacafe\.com/watch/(?P<metacafeid>\d+)/?(:?.+/?)')
        self.add_inline(md, 'veoh', Veoh,
            r'http://www\.veoh\.com/\S*(#watch%3D|watch/)(?P<veohid>\w+)')
        self.add_inline(md, 'vimeo', Vimeo,
            r'http://(www.|)vimeo\.com/(?P<vimeoid>\d+)\S*')
        self.add_inline(md, 'yahoo', Yahoo,
            r'http://screen\.yahoo\.com/.+/?')
        self.add_inline(md, 'youtube', Youtube,
            r'https?://www\.youtube\.com/watch\?\S*v=(?P<youtubeid>\S[^&/]+)')
        self.add_inline(md, 'youtube_short', Youtube,
            r'https?://youtu\.be/(?P<youtubeid>\S[^?&/]+)?')

class VideoBProcessor(BlockProcessor):
    def __init__(self, md, name, klass, patt, config):
        self.md    = md
        self.name  = name
        self.klass = klass(config)
        self.RE    = re.compile(patt)
    
    def test(self, parent, block):
        return bool(self.RE.search(block))

    def run(self, parent, blocks):
        block = blocks.pop(0)
        
        m = self.RE.search(block)

        before = block[:m.start()]
        after  = block[m.end():]

        if before:
            self.parser.parseBlocks(parent, [before])
        
        el = self.klass.handleMatch(m)
        parent.append(el)

        if after:
            blocks.insert(0, after)

class Dailymotion(object):
    def __init__(self, config):
        self.config = config
    def handleMatch(self, m):
        url = 'http://www.dailymotion.com/embed/video/%s' % m.group('dailymotionid')
        width = self.config['dailymotion_width'][0]
        height = self.config['dailymotion_height'][0]
        return render_iframe(url, width, height)


class Metacafe(object):
    def __init__(self, config):
        self.config = config
    def handleMatch(self, m):
        url = 'http://www.metacafe.com/embed/%s/' % m.group('metacafeid')
        width = self.config['metacafe_width'][0]
        height = self.config['metacafe_height'][0]
        return render_iframe(url, width, height)


class Veoh(object):
    def __init__(self, config):
        self.config = config
    def handleMatch(self, m):
        url = 'http://www.veoh.com/videodetails2.swf?permalinkId=%s' % m.group('veohid')
        width = self.config['veoh_width'][0]
        height = self.config['veoh_height'][0]
        return flash_object(url, width, height)


class Vimeo(object):
    def __init__(self, config):
        self.config = config
    def handleMatch(self, m):
        url = 'http://player.vimeo.com/video/%s' % m.group('vimeoid')
        width = self.config['vimeo_width'][0]
        height = self.config['vimeo_height'][0]
        return render_iframe(url, width, height)


class Yahoo(object):
    def __init__(self, config):
        self.config = config
    def handleMatch(self, m):
        url = m.string + '?format=embed&player_autoplay=false'
        width = self.config['yahoo_width'][0]
        height = self.config['yahoo_height'][0]
        return render_iframe(url, width, height)


class Youtube(object):
    def __init__(self, config):
        self.config = config
    def handleMatch(self, m):
        url = 'http://www.youtube.com/embed/%s' % m.group('youtubeid')
        width = self.config['youtube_width'][0]
        height = self.config['youtube_height'][0]
        return render_iframe(url, width, height)


def render_iframe(url, width, height):
    iframe = etree.Element('iframe')
    iframe.set('width', width)
    iframe.set('height', height)
    iframe.set('src', url)
    iframe.set('allowfullscreen', 'true')
    iframe.set('frameborder', '0')
    return iframe


def flash_object(url, width, height):
    obj = etree.Element('object')
    obj.set('type', 'application/x-shockwave-flash')
    obj.set('width', width)
    obj.set('height', height)
    obj.set('data', url)
    param = etree.Element('param')
    param.set('name', 'movie')
    param.set('value', url)
    obj.append(param)
    param = etree.Element('param')
    param.set('name', 'allowFullScreen')
    param.set('value', 'true')
    obj.append(param)
    return obj


def makeExtension(configs=None):
    return VideoExtension(configs=configs)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
