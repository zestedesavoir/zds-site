#! /usr/bin/env python

import markdown
from markdown.treeprocessors import Treeprocessor
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

def makeExtension(configs={}):
    return SmartImgExtension(configs=configs)
