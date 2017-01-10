import markdown
from markdown import inlinepatterns, util, Extension
from markdown.blockprocessors import BlockProcessor
import re


class MathJaxPattern(inlinepatterns.Pattern):
    def __init__(self):
        inlinepatterns.Pattern.__init__(self, r'(?<!\\)\$([^\n]+?)(?<!\\)\$')

    def handleMatch(self, m):
        node = util.etree.Element('span')
        node.text = util.AtomicString("$" + m.group(2) + "$")
        return node


class MathJaxBlock(BlockProcessor):
    def __init__(self, parser):
        BlockProcessor.__init__(self, parser)
        self.re = re.compile(r'(?:^|\n)\$\$.+\$\$(\n|$)', re.DOTALL | re.MULTILINE | re.UNICODE)

    def test(self, parent, block):
        return self.re.search(block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.re.search(block)
        before = block[:m.start()]
        after = block[m.end():]
        block = block[m.start():m.end()]

        if before:
            self.parser.parseBlocks(parent, [before])
        dnode = util.etree.SubElement(parent, 'div')

        dnode.set('class', "mathjax-wrapper")
        node = markdown.util.etree.SubElement(dnode, "mathjax")
        node.text = markdown.util.AtomicString(block.strip())

        if after:
            blocks.insert(0, after)


class MathJaxExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.add('mathjax', MathJaxPattern(), '<escape')
        md.parser.blockprocessors.add('mathjax', MathJaxBlock(md.parser), '>reference')


def makeExtension(*args, **kwargs):
    return MathJaxExtension(*args, **kwargs)
