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

        self.REStart = re.compile(r'(^|\n)' + re.escape(startExpr))
        self.REEnd   = re.compile(re.escape(endExpr) + r'(\n|$)')
        self.contentAlign = contentAlign

    def test(self, parent, block):
        return bool(self.REStart.search(block))

    def run(self, parent, blocks):
        
        FirstBlock = blocks[0]
        m = self.REStart.search(FirstBlock)
        if not m:
            return False
        StartBlock = (0, m.start(), m.end())
        
        EndBlock = (-1, -1, -1)
        for i in range(len(blocks)):
            if i == 0 :
                txt = FirstBlock[m.end()+1:]
                dec = m.end()-m.start()+1
            else:
                txt = blocks[i]
                dec = 0

            mEnd = self.REEnd.search(txt)
            if mEnd:
                EndBlock = (i, mEnd.start() + dec, mEnd.end() + dec)
                break

        if EndBlock[0] < 0 :
            return False
        Before = FirstBlock[:StartBlock[1]]
        Content = []
        After = blocks[EndBlock[0]][EndBlock[2]:]
        for i in range(0,EndBlock[0]+1):
            blck = blocks.pop(0)
            
            if i == StartBlock[0]:
                startIndex = StartBlock[2]
            else:
                startIndex = 0
            
            if i == EndBlock[0]:
                endIndex = EndBlock[1]  
            else:
                endIndex = len(blck)
            
            Content.append(blck[startIndex: endIndex])
        
        Content = "\n\n".join(Content)

        if Before:
            self.parser.parseBlocks(parent, [Before])
        
        sibling = self.lastChild(parent)
        if sibling and sibling.tag == "div" and "align" in sibling.attrib and sibling.attrib["align"] == self.contentAlign :
            h= sibling

            if h.text:
                h.text += '\n'
        else:
            h = util.etree.SubElement(parent, 'div')
            h.set("align", self.contentAlign)
        
        self.parser.parseChunk(h, Content)
        
        if After:
            blocks.insert(0, After)

class AlignExtension(markdown.extensions.Extension):
    """Adds align extension to Markdown class."""

    def extendMarkdown(self, md, md_globals):
        """Modifies inline patterns."""
        md.registerExtension(self)
        md.parser.blockprocessors.add('rightalign', AlignProcessor(md.parser, "->", "->", "right"),'_begin')
        md.parser.blockprocessors.add('centeralign', AlignProcessor(md.parser, "->", "<-", "center"),'_begin')

def makeExtension(configs={}):
    return AlignExtension(configs=dict(configs))

