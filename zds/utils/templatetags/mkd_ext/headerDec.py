# -*- coding: utf-8 -*-
import markdown
import re

def makeExtension(configs=None) :
    return DownHeaderExtension(configs=configs)
   
class DownHeaderExtension(markdown.Extension):
    def __init__(self, configs):
        self.configs={"OFFSET": 1}
        for key, value in configs.iteritems():
            self.configs[key] = value
    
    def extendMarkdown(self, md, md_globals):
        # VERY DANGEROUS !
        md.parser.blockprocessors["hashheader"].RE = re.compile(r'(^|\n)(?P<level>#{1,' + str(6 - self.configs["OFFSET"]) + r'})[^#](?P<header>.*?)#*(\n|$)')
        md.treeprocessors.add('downheader', DownHeaderProcessor(self.configs["OFFSET"]), '_end')

class DownHeaderProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, offset=1):
        markdown.treeprocessors.Treeprocessor.__init__(self)
        self.offset = offset
    def run(self, node):
        expr = re.compile('h(\d)')
        for child in node.getiterator():
            match = expr.match(child.tag)
            if match:
                child.tag = 'h' + str(min(6, int(match.group(1))+self.offset))
        return node
