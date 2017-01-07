from __future__ import unicode_literals
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.extensions.codehilite import CodeHilite, CodeHiliteExtension
from markdown import util
import re


class FencedCodeExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.parser.blockprocessors.add('fenced_code_block', FencedBlockProcessor(md), "_begin")


class FencedBlockProcessor(BlockProcessor):
    STARTING_RE = r'(?P<fence>^(?:~{3,}|`{3,}))'
    LANG_RE = r'(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*))?'
    ARG_ELEMENT = r'(([a-z_]+[ ]*=[ ]*)+(((?P<quot>(")|(\'))([0-9\- ]+)(?P=quot))|([0-9]+))[ ]*)'
    ARG_LIST_RE = r'(?P<arglist>' + ARG_ELEMENT + r'*)'
    CODE_WRAP = '<pre><code%s>%s</code></pre>'
    LANG_TAG = ' class="%s"'

    def __init__(self, md):
        BlockProcessor.__init__(self, md.parser)
        self.re = re.compile(
                r'(^|\n)' + self.STARTING_RE + r'[ ]*' +  # Opening ``` or ~~~
                self.LANG_RE + r'(?P<interspace>[ ]*)' +  # Optional {, and lang
                self.ARG_LIST_RE +  # Optional arg list
                r'}?[ ]*(\n|$)', re.MULTILINE | re.UNICODE)
        self.checked_for_codehilite = False
        self.codehilite_conf = {}
        self.md = md

    def test(self, parent, block):
        return bool(self.re.search(block))

    def _parse_argument(self, m):
        gd = m.groupdict()

        fence = gd['fence']
        lang = gd['lang']
        arglist = gd['arglist']
        interspace = gd['interspace']
        if lang and arglist and len(interspace) == 0:
            arglist = lang + arglist
            lang = ""
        # Parse arguments
        linenostart = (1,)
        hl_lines = ()
        for m_arg in re.compile(self.ARG_ELEMENT).finditer(arglist):
            kind, args = m_arg.group(0).split("=")
            args = args.strip()
            if args[0] in """"'""":
                elements = set()
                for e in args[1:-1].split(" "):
                    e = e.strip()
                    if e:
                        if "-" in e:
                            e1, e2 = e.split("-")
                            elements.update(range(int(e1), int(e2) + 1))
                        else:
                            elements.add(int(e))
                elements = tuple(sorted(elements))
            else:
                elements = (int(args),)
            if kind == "linenostart":
                linenostart = elements
            elif kind == "hl_lines":
                hl_lines = elements
            else:
                # unknown argument
                return False
        linenostart, = linenostart
        return fence, lang, linenostart, hl_lines

    def _extract_content_position(self, blocks, fence, m):
        first_block = blocks[0]
        re_end = re.compile(r'(^|\n)' + re.escape(fence) + r'[ ]*(\n|$)')

        start_block = (0, m.start(), m.end())
        end_block = (-1, -1, -1)
        for i in range(len(blocks)):
            if i == 0:
                txt = first_block[m.end() + 1:]
                dec = m.end() + 1
            else:
                txt = blocks[i]
                dec = 0
            m_end = re_end.search(txt)
            if m_end:
                end_block = (i, m_end.start() + dec, m_end.end() + dec)
                break
        return start_block, end_block

    def _extract_content(self, blocks, fence, m):
        # Search end
        first_block = blocks[0]

        start_block, end_block = self._extract_content_position(blocks, fence, m)

        if end_block[0] < 0:
            # Block not ended, do not transform
            return None, None, None

        # Split blocks into before/content aligned/ending
        before = first_block[:start_block[1]]
        content = []
        after = blocks[end_block[0]][end_block[2]:]

        for i in range(start_block[0], end_block[0] + 1):
            block = blocks.pop(0)

            if i == start_block[0]:
                start_index = start_block[2]
            else:
                start_index = 0

            if i == end_block[0]:
                end_index = end_block[1]
            else:
                end_index = len(block)

            content.append(block[start_index: end_index + 1])
            if i == end_block[0]:
                break

        content = "\n\n".join(content)
        return before, content, after

    def extract_code(self, content, lang, hl_lines, linenostart):
        # If config is not empty, then the codehighlite extension
        # is enabled, so we call it to highlight the code
        if self.codehilite_conf:
            highliter = CodeHilite(content,
                                   linenums=self.codehilite_conf['linenums'][0],
                                   guess_lang=self.codehilite_conf['guess_lang'][0],
                                   css_class=self.codehilite_conf['css_class'][0],
                                   style=self.codehilite_conf['pygments_style'][0],
                                   lang=(lang or None),
                                   noclasses=self.codehilite_conf['noclasses'][0],
                                   hl_lines=hl_lines,
                                   linenostart=linenostart)

            code = highliter.hilite()
        else:
            if lang:
                cls_lang = self.LANG_TAG % lang
            else:
                cls_lang = ''
            code = self.CODE_WRAP % (cls_lang, self._escape(content))
        return code

    def run(self, parent, blocks):
        first_block = blocks[0]
        m = self.re.search(first_block)
        if not m:  # pragma: no cover
            # Run should only be fired if test() return True, then this should never append
            # Do not raise an exception because exception should never be generated.
            return False

        fence, lang, linenostart, hl_lines = self._parse_argument(m)

        before, content, after = self._extract_content(blocks, fence, m)

        if before is None:
            return False

        # Check for code hilite extension
        if not self.checked_for_codehilite:
            for ext in self.md.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehilite_conf = ext.config
                    break

            self.checked_for_codehilite = True

        if before:
            self.parser.parseBlocks(parent, [before])

        code = self.extract_code(content, lang, hl_lines, linenostart)

        div_wrapper = util.etree.SubElement(parent, 'div')
        div_wrapper.text = util.RawHTMLString(code)
        if after:
            blocks.insert(0, after)

    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(*args, **kwargs):
    return FencedCodeExtension(*args, **kwargs)
