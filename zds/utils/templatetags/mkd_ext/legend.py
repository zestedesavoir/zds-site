#! /usr/bin/env python

import markdown
from markdown.blockprocessors import BlockProcessor
import logging
import re
from markdown import util

class LegendProcessor(BlockProcessor):
    """ Legend Center. """

    RE = re.compile(r'^(Table[ ]{0,1})*\:(?P<txtlegend>.*?)(\n|$)')

    def test(self, parent, block):
        sibling = self.lastChild(parent)
        return sibling and sibling.tag == "table" and  bool(self.RE.search(block))

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)
        print "la"
        if m:
            before = block[:m.start()] # All lines before header
            after = block[m.end():]    # All lines after header
            sibling = self.lastChild(parent)
            print parent
            print sibling
            if before:
                print before
                self.parser.parseBlocks(parent,[before])
            sibling = self.lastChild(parent)
            print sibling
            if sibling and sibling.tag == "table" :
                print "ici"
                h = util.etree.Element('caption')
                sibling.insert(0,h)
                self.parser.parseChunk(h, m.group('txtlegend'))
            if after:
                blocks.insert(0, after)
        else:
            logger.warn("We've got a problem center: %r" % block)

class LegendExtension(markdown.extensions.Extension):
    """Adds Legend extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.registerExtension(self)
        md.parser.blockprocessors.add('legend',LegendProcessor(md.parser),'>grid-table')

def makeExtension(configs={}):
    return LegendExtension(configs=dict(configs))

