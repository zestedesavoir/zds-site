from __future__ import unicode_literals
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree
import re


class CustomBlockExtension(Extension):
    """ Custom block extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add CustomBlock to Markdown instance. """
        md.registerExtension(self)

        md.parser.blockprocessors.add( 'customblock', CustomBlockProcessor(md.parser,
            {
                "secret" : "spoiler",
                "s" : "spoiler",
                "information" : "information ico-after",
                "i" : "information ico-after",
                "question" : "question ico-after",
                "q" : "question ico-after",
                "attention" : "attention ico-after", 
                "a" : "attention ico-after", 
                "erreur" : "erreur ico-after",
                "e" : "erreur ico-after"
            }), '_begin')


class CustomBlockProcessor(BlockProcessor):

    RE = re.compile(r'(?:^|\n)\[\[?([\w\-]+)?\]\](\n|$)')
    def __init__(self, parser,classType):
        BlockProcessor.__init__(self,parser)
        self.classType = classType

    def test(self, parent, block):
        sibling = self.lastChild(parent)
        m = self.RE.search(block)
        if m:
            classTypeSup = m.group(0).lower().strip()[2:-2]
        return (m and classTypeSup in self.classType.keys()) or \
            (block.startswith('|' ) and sibling and \
                sibling.get('class', '').find("CustomBlock") != -1)
    def extractBlock(self,m,block):
        if m:
            before = block[:m.start()]
            klass = self.classType[m.group(0).lower().strip()[2:-2]]
       	    block = block[m.end():]  # removes the first line
        else:
            before = None
            klass = None
        cblck=[]
        theRest=[]
        inBlck=True
        for line in block.split("\n"):
            if inBlck and len(line.strip()) >= 1 and line.strip()[0] == "|":
                cblck.append(line[1:])
            else:
                theRest.append(line)
                inBlck = False
        return before, klass, "\n".join(cblck), "\n".join(theRest)

    def run(self, parent, blocks):
        sibling = self.lastChild(parent)
        block = blocks.pop(0)
        m = self.RE.search(block)

        before, klass, block, theRest = self.extractBlock(m,block)
        if before:
            self.parser.parseBlocks(parent, [before])
        
        if m or not sibling:
            div = etree.SubElement(parent, 'div')
            div.set('class', '%s' % ( klass,))
        else:
            div = sibling
        #self.parser.state.set("CustomBlock")
        self.parser.parseChunk(div, block)
        #self.parser.state.reset()
        if theRest:
            blocks.insert(0, theRest)



def makeExtension(configs={}):
    return CustomBlockExtension(configs=configs)
