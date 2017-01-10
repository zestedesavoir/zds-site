# -*- coding: utf-8 -*-
import markdown
import re


class DownHeaderExtension(markdown.Extension):
    def __init__(self, *args, **kwargs):
        self.config = {"offset": [1, "header offset to apply"]}
        markdown.Extension.__init__(self, *args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        # VERY DANGEROUS !
        md.parser.blockprocessors["hashheader"].RE = re.compile(
            r'(^|\n)(?P<level>#{1,%d})(?P<header>.*?)#*(\n|$)' % (6 - self.getConfig("offset")))
        md.treeprocessors.add('downheader', DownHeaderProcessor(self.getConfig("offset")), '_end')


class DownHeaderProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, offset=1):
        markdown.treeprocessors.Treeprocessor.__init__(self)
        self.offset = offset

    def run(self, node):
        expr = re.compile('h(\d)')
        for child in node.getiterator():
            match = expr.match(child.tag)
            if match:
                child.tag = 'h' + str(min(6, int(match.group(1)) + self.offset))
        return node
