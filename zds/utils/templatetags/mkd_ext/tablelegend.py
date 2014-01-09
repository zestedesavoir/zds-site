#! /usr/bin/env python

import markdown
from markdown.blockprocessors import BlockProcessor
import logging
import re
from markdown import util

class TableLegendProcessor(BlockProcessor):
    """ Table legend """

    RE = re.compile(r'(^|\n)(Table[ ]{0,1})*\:(?P<txtlegend>.*?)(\n|$)')
    def __init__(self, parser, totest):
        BlockProcessor.__init__(self, parser)
        self.totest = totest

    def test(self, parent, block):
        m = self.RE.search(block)
        if not bool(m):
            return False
        
        sibling = self.lastChild(parent)
        PreviousWillBeTable = False # sibling and sibling.tag== "table"
        for extTab in self.totest:
            PreviousWillBeTable = PreviousWillBeTable or extTab.test(parent,block[:m.start()])
        
        return PreviousWillBeTable

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)
        if m:
            before = block[:m.start()] # All lines before header
            after = block[m.end():]    # All lines after header
            sibling = self.lastChild(parent)
            if before:
                self.parser.parseBlocks(parent,[before])
            sibling = self.lastChild(parent)
            if sibling and sibling.tag == "table" :
                h = util.etree.Element('caption')
                sibling.insert(0,h)
                self.parser.parseChunk(h, m.group('txtlegend'))
            if after:
                blocks.insert(0, after)
        else:
            logger.warn("We've got a problem center: %r" % block)

class TableLegendExtension(markdown.extensions.Extension):
    """Adds Legend extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.registerExtension(self)
        toTest=[]
        if "grid-table" in md.parser.blockprocessors:
            toTest.append(md.parser.blockprocessors["grid-table"])
        if "table" in md.parser.blockprocessors:
            toTest.append(md.parser.blockprocessors["table"])
        md.parser.blockprocessors.add('table-legend',TableLegendProcessor(md.parser, toTest),'_begin')

def makeExtension(configs={}):
    return TableLegendExtension(configs=dict(configs))

