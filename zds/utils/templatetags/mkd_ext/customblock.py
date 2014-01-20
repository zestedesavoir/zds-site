from __future__ import unicode_literals
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree
import re


class CustomBlockExtension(Extension):
    """ Custom block extension for Python-Markdown. """

    def __init__(self, configs):
        self.configs = configs

    def extendMarkdown(self, md, md_globals):
        """ Add CustomBlock to Markdown instance. """
        md.registerExtension(self)

        for key, value in self.configs.iteritems():
            md.parser.blockprocessors.add( 'customblock-'+ key, CustomBlockProcessor(md.parser, key, value), '_begin')


class CustomBlockProcessor(BlockProcessor):

    def __init__(self, parser,repart, classType):
        BlockProcessor.__init__(self,parser)
        self.classType = classType
        self.RE = re.compile( r'(?:^|\n)\[\[' + repart + r'\]\](\n|$)')

    def test(self, parent, block):
        return self.RE.search(block)
    
    def extractBlock(self,m,block):
        before = block[:m.start()]
       	block = block[m.end():]  # removes the first line
        
        cblck=[]
        theRest=[]
        inBlck=True
        
        for line in block.split("\n"):
            if inBlck and len(line.strip()) >= 1 and line[0] == "|":
                if len(line) <= 1 :
                    cblck.append(line[1:])
                elif line[1] == ' ':
                    cblck.append(line[2:])
                else:
                    cblck.append(line[1:])
            else:
                theRest.append(line)
                inBlck = False
        
        return before, "\n".join(cblck), "\n".join(theRest)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)

        before, block, theRest = self.extractBlock(m,block)
        
        if before:
            self.parser.parseBlocks(parent, [before])
        
        div = etree.SubElement(parent, 'div')
        div.set('class', '%s' % ( self.classType,))
        
        self.parser.parseChunk(div, block)
        
        if theRest:
            blocks.insert(0, theRest)

def makeExtension(configs={}):
    return CustomBlockExtension(configs=configs)
