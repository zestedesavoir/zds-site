#! /usr/bin/env python

import markdown
from markdown.blockprocessors import BlockProcessor
import logging
import re
from markdown import util
import xml.etree.ElementTree as ET

class CodeLegendProcessor(BlockProcessor):
    """ Code legend """

    RE = re.compile(r'(^|\n)(Code[ ]{0,1})*\:(?P<txtlegend>.*?)(\n|$)')
    def __init__(self, parser, md):
        BlockProcessor.__init__(self, parser)
        self.md = md

    def test(self, parent, block):
        m = self.RE.search(block)
        return bool(m)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)
        if m:
            before = block[:m.start()] # All lines before header
            after = block[m.end():]    # All lines after header
            sibling = self.lastChild(parent)
            if before:
                res= self.parser.parseBlocks(parent,[before])
            sibling = self.lastChild(parent)
            if self.test_previous_is_code(sibling) :
                #h = util.etree.Element('caption')
                #sibling.insert(0,h)
                oldElem = sibling
                parent.remove(oldElem)
                nFig = util.etree.Element("figure")
                nFigCaption = util.etree.Element("figurecaption")

                self.parser.parseChunk(nFigCaption, m.group('txtlegend'))
                nFig.append(oldElem)
                nFig.append(nFigCaption)
                parent.append(nFig)
            else:
                blocks.insert(0,block[m.start():])
                return False
            if after:
                blocks.insert(0, after)
        else:
            logger.warn("We've got a problem center: %r" % block)
    def test_previous_is_code(self, sibling):
        # standard code
        if sibling is not None and sibling.tag == u"pre" and len(sibling) and sibling[0].tag == u"code" :
            return True
        # fenced code
        if sibling is not None and sibling.tag == u"p":
            hs = self.md.htmlStash
            for i in range(hs.html_counter):
                if sibling.text == hs.get_placeholder(i) :
                    Teste = ET.fromstring(hs.rawHtmlBlocks[i][0])
                    if Teste is not None and Teste.tag=="table" and "class" in Teste.attrib and Teste.attrib["class"] == "codehilitetable":
                        return True
        return False
class CodeLegendExtension(markdown.extensions.Extension):
    """Adds Legend extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.registerExtension(self)
        md.parser.blockprocessors.add('code-legend',CodeLegendProcessor(md.parser, md),'_begin')

def makeExtension(configs={}):
    return CodeLegendExtension(configs=dict(configs))

