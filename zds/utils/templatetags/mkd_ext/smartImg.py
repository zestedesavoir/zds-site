#! /usr/bin/env python

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.blockprocessors import BlockProcessor
import re
from markdown import util
class SmartImgProcessor(Treeprocessor):
    def __init__(self, parser, configs):
        Treeprocessor.__init__(self, parser)

        self.configs = configs
    
    def run(self, root):
        
        elemsToInspect = [root]
        while len(elemsToInspect) > 0:
            elem = elemsToInspect.pop()
            for nelem in elem:
                if nelem.tag in self.configs["PARENTS"]:
                    elemsToInspect.append(nelem)
                elif nelem.tag == "p" and len(list(nelem.itertext())) == 0 :
                    lelems = list(nelem.iter())

                    if     (len(lelems) == 1 or (len(lelems)==2 and lelems[0] is nelem)) \
                            and lelems[-1].tag == "img" \
                            and lelems[-1].attrib["alt"] != "" \
                            and not (lelems[-1].attrib["src"] in self.configs["IGNORING_IMG"]):
                        oldImg = lelems[-1]
                        nelem.remove(oldImg)
                        nFig = util.etree.Element("figure")
                        nFigCaption = util.etree.Element("figurecaption")
                        nFigCaption.text = oldImg.attrib["alt"]
                        oldImg.attrib["alt"]=""
                        nFig.append(oldImg)
                        nFig.append(nFigCaption)
                        nelem.append(nFig)

        return root


class FigureProcessor(BlockProcessor):
    def __init__(self, parser, md):
        BlockProcessor.__init__(self, parser)
        self.md = md
        self.imPro = md.inlinePatterns["image_link"]
        self.RE = re.compile(r'\n(Figure[ ]{0,1})*\:(?P<txtlegend>.*?)(\n|$)')

    def test(self, parent, block):
        mImg = self.imPro.getCompiledRegExp().match(block)
        if mImg is None:
            return False
        mLeg = self.RE.search(block)
        if mLeg is None:
            return False
        return mImg.start(11) == mLeg.start()

    def run(self, parent, blocks):
        block = blocks.pop(0)
        mImg = self.imPro.getCompiledRegExp().match(block)
        mLeg = self.RE.search(block)
        before = block[:mImg.end(1)]
        after = block[mLeg.end():]
        content = block[mImg.start():mLeg.end()]
        contentImg = block[mImg.end(1):mLeg.start()]
        if before:
            self.parser.parseBlocks(parent, [before])
        nFig = util.etree.Element("figure")
        nFigCaption = util.etree.Element("figurecaption")
        self.parser.parseChunk(nFigCaption, mLeg.group('txtlegend'))
        self.parser.parseChunk(nFig, contentImg)
        nFig.append(nFigCaption)
        parent.append(nFig)
        if after:
            blocks.insert(0,after)

class SmartImgExtension(markdown.extensions.Extension):
    def __init__(self, configs={}):
        self.configs = {
            "IGNORING_IMG" : [],
            "PARENTS"      : [],
            }
        for key, value in configs.iteritems():
            self.configs[key] = value
        if "div" not in self.configs["PARENTS"]:
            self.configs["PARENTS"].append("div")
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.treeprocessors.add('smart-img', SmartImgProcessor(md.parser,self.configs),"_end")
        md.parser.blockprocessors.add('figure-processor', FigureProcessor(md.parser,md),"_begin")

def makeExtension(configs={}):
    return SmartImgExtension(configs=configs)
