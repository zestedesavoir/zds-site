import re
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension


class CommentsExtension(Extension):
    def __init__(self, *args, **kwargs):
        self.config = {"start_tag": ["<--COMMENTS", ""],
                       "end_tag":   ["COMMENTS-->", ""]}
        Extension.__init__(self, *args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.parser.blockprocessors.add("comments",
                                      CommentsBlockProcessor(md, self.getConfig("start_tag"),
                                                             self.getConfig("end_tag")),
                                      ">fenced_code_block")


class CommentsBlockProcessor(BlockProcessor):
    def __init__(self, md, start_tag, end_tag):
        BlockProcessor.__init__(self, md.parser)

        StaEsc = re.escape(start_tag)
        EndEsc = re.escape(end_tag)

        self.START_RE = re.compile(StaEsc, re.MULTILINE | re.DOTALL)
        self.RE = re.compile(StaEsc + r'.*?' + EndEsc, re.MULTILINE | re.DOTALL)

    def test(self, parent, block):
        return bool(self.START_RE.search(block))

    def run(self, parent, blocks):
        text = "\n\n".join(blocks)

        m = self.RE.search(text)

        if m is None:
            return False
        text = "%s%s" % (text[:m.start()], text[m.end():])
        del blocks[:]
        blocks.extend(text.split("\n\n"))


def makeExtension(*args, **kwargs):
    return CommentsExtension(*args, **kwargs)
