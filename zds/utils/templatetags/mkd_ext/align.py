#! /usr/bin/env python

import markdown
from markdown.blockprocessors import BlockProcessor
import logging
import re
from markdown import util

class AlignProcessor(BlockProcessor):
    """ Process Align. """

    def __init__(self, parser, startExpr, endExpr, contentAlign):
        BlockProcessor.__init__(self, parser)

        self.RE = re.compile(r'(^|\n)' + re.escape(startExpr) + r'(?P<txt>.*?)' + re.escape(endExpr) + r'(\n|$)', re.MULTILINE | re.DOTALL)
        self.contentAlign = contentAlign

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
            if sibling and sibling.tag == "div" and "align" in sibling.attrib and sibling.attrib["align"] == self.contentAlign :
                h= sibling
                if h.text:
                    h.text += '\n'
            else:
                h = util.etree.SubElement(parent, 'div')
                h.set("align", self.contentAlign)
            self.parser.parseChunk(h, m.group('txt'))
            if after:
                blocks.insert(0, after)
        else:
            blocks.insert(0,block)
            return False

class AlignExtension(markdown.extensions.Extension):
    """Adds align extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.registerExtension(self)
        md.parser.blockprocessors.add('rightalign', AlignProcessor(md.parser, "->", "->", "right"),'_begin')
        md.parser.blockprocessors.add('centeralign', AlignProcessor(md.parser, "->", "<-", "center"),'_begin')

def makeExtension(configs={}):
    return AlignExtension(configs=dict(configs))

