from __future__ import unicode_literals
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree
import re


class CustomBlockExtension(Extension):
    """ Custom block extension for Python-Markdown. """

    def __init__(self, *args, **kwargs):
        self.config = {
            'classes': [{}, 'A mapping from element re to html class.'],
        }
        Extension.__init__(self, *args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        """ Add CustomBlock to Markdown instance. """
        md.registerExtension(self)

        for key, value in self.getConfig("classes").items():
            md.parser.blockprocessors.add('customblock-' + key,
                                          CustomBlockProcessor(md.parser, key, value),
                                          '>reference')


class CustomBlockProcessor(BlockProcessor):
    def __init__(self, parser, repart, classType):
        BlockProcessor.__init__(self, parser)
        self.classType = classType
        self.RE = re.compile(r'(?:^|\n)\[\[' + repart + r'\]\](\n|$)')

    def test(self, parent, block):
        return self.RE.search(block)

    def extractBlock(self, m, block):
        before = block[:m.start()]
        block = block[m.end():]  # removes the first line

        content = []
        rest = []
        in_block = True

        for line in block.split("\n"):
            if in_block and len(line.strip()) >= 1 and line[0] == "|":
                if len(line) <= 1 or line[1] != ' ':
                    content.append(line[1:])
                else:
                    content.append(line[2:])
            else:
                rest.append(line)
                in_block = False

        return before, "\n".join(content), "\n".join(rest)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)

        before, block, rest = self.extractBlock(m, block)

        if before:
            self.parser.parseBlocks(parent, [before])

        div = etree.SubElement(parent, 'div')
        div.set('class', '%s' % (self.classType,))

        self.parser.parseChunk(div, block)

        if rest:
            blocks.insert(0, rest)


def makeExtension(*args, **kwargs):
    return CustomBlockExtension(*args, **kwargs)
