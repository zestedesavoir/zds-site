#! /usr/bin/env python

import markdown
#from markdown.inlinepatterns import SimpleTagPattern
from markdown.blockprocessors import BlockProcessor
# Small extension to parse `-> right align ->` (cgabard)
import logging
import re
from markdown import util

class RightAlignProcessor(BlockProcessor):
    """ Process Center. """

    RE = re.compile(r'(^|\n)->(?P<txtright>.*?)->(\n|$)', re.MULTILINE|re.DOTALL)

    def test(self, parent, block):
        return bool(self.RE.search(block))

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)
        if m:
            before = block[:m.start()] # All lines before header
            after = block[m.end():]    # All lines after header
            if before:
                self.parser.parseBlocks(parent, [before])
            sibling = self.lastChild(parent)
            if sibling and sibling.tag == "div" and "align" in sibling.attrib and sibling.attrib["align"] == "right" :
                h= sibling
                if h.text:
                    h.text += '\n'
            else:
                h = util.etree.SubElement(parent, 'div')
                h.set("align","right")
            #h.text = m.group('txtright').strip()
            self.parser.parseChunk(h, m.group('txtright'))
            if after:
                blocks.insert(0, after)
        else:
            logger.warn("We've got a problem center: %r" % block)

class RightAlignExtension(markdown.extensions.Extension):
    """Adds Rigth align extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.registerExtension(self)
        md.parser.blockprocessors.add('rightalign',RightAlignProcessor(md.parser),'_begin')

def makeExtension(configs={}):
    return RightAlignExtension(configs=dict(configs))

