from markdown import Extension
from markdown.blockprocessors import BlockProcessor
import re
from markdown.util import etree

LEGEND_RE = r"(%s\s*)?:\s*(?P<txtlegend>.*)"


class AutoFigureProcessor(BlockProcessor):
    def __init__(self, md):
        BlockProcessor.__init__(self, md.parser)
        self.md = md
        legend_re = LEGEND_RE % "Figure"
        self.re = re.compile(r"^%s(\n%s)?$" % (md.inlinePatterns["image_link"].pattern, legend_re),
                             re.MULTILINE | re.DOTALL | re.UNICODE)
        self.legend_re = re.compile(r"^%s$" % legend_re, re.MULTILINE | re.DOTALL | re.UNICODE)

    def test(self, parent, block):
        return self.re.match(block)

    def run(self, parent, blocks):
        b = blocks.pop(0)
        m = self.re.match(b)
        if not m:  # pragma: no cover
            # Should not happen
            return False
        if m.group("txtlegend") is None:
            if blocks:
                ml = self.legend_re.match(blocks[0])
            else:
                ml = None

            if ml:
                blocks.pop(0)
                alt = m.group(1)
                caption = ml.group("txtlegend")
            else:
                alt = ""
                caption = m.group(1)
        else:
            alt = m.group(1)
            caption = m.group("txtlegend")

        # Insert figure and alt as legend
        f = etree.SubElement(parent, 'figure')
        f.text = "![%s](%s)" % (alt, m.group(8))
        figcaption = etree.Element("figcaption")
        figcaption.text = caption

        f.append(figcaption)


class InnerProcessor(BlockProcessor):
    def __init__(self, md, legend_name, block_src):
        BlockProcessor.__init__(self, md.parser)
        self.re_legend = re.compile(r"^%s$" % (LEGEND_RE % legend_name), re.MULTILINE | re.DOTALL)
        self.block_src = block_src

    def test(self, parent, block):
        return self.block_src.test(parent, block)

    def run(self, parent, blocks):
        first_block = blocks[0]
        m = self.re_legend.search(first_block)
        if m:
            blocks[0] = first_block[:m.start()].rstrip()
        response = self.block_src.run(parent, blocks)
        if response is False:
            return False
        if not m and len(blocks) > 0:
            first_block = blocks[0].strip()
            m = self.re_legend.match(first_block)
            if m:
                blocks.pop(0)
        if m:
            sibling = self.lastChild(parent)
            parent.remove(sibling)
            fig = etree.SubElement(parent, 'figure')
            fig.append(sibling)
            fig_caption = etree.Element("figcaption")
            fig_caption.text = m.group("txtlegend")
            fig.append(fig_caption)


class SmartLegendExtension(Extension):
    def __init__(self, *args, **kwargs):
        Extension.__init__(self, *args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.parser.blockprocessors.add('auto-figure', AutoFigureProcessor(md), '_begin')
        md.parser.blockprocessors['quote'] = InnerProcessor(md, "Source", md.parser.blockprocessors['quote'])
        md.parser.blockprocessors['table'] = InnerProcessor(md, "Table", md.parser.blockprocessors['table'])
        md.parser.blockprocessors['grid-table'] = InnerProcessor(md, "Table", md.parser.blockprocessors['grid-table'])
        md.parser.blockprocessors['mathjax'] = InnerProcessor(md, "Equation", md.parser.blockprocessors['mathjax'])
        md.parser.blockprocessors['fenced_code_block'] = InnerProcessor(md, "Code",
                                                                        md.parser.blockprocessors['fenced_code_block'])
        for blockname, processor in md.parser.blockprocessors.items():
            if blockname.startswith("video-"):
                md.parser.blockprocessors[blockname] = InnerProcessor(md, "Video", processor)


def makeExtension(*args, **kwargs):
    return SmartLegendExtension(*args, **kwargs)
