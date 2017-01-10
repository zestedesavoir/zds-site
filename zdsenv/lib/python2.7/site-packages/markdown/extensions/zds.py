from __future__ import absolute_import
from __future__ import unicode_literals
from . import Extension

from .abbr import AbbrExtension
from .align import AlignExtension
from .codehilite import CodeHiliteExtension
from .comments import CommentsExtension
from .customblock import CustomBlockExtension
from .delext import DelExtension
from .emoticons import EmoticonExtension
from .fenced_code import FencedCodeExtension
from .footnotes import FootnoteExtension
from .french_typography import FrenchTypographyExtension
from .grid_tables import GridTableExtension
from .header_dec import DownHeaderExtension
from .kbd import KbdExtension
from .mathjax import MathJaxExtension
from .ping import PingExtension
from .smart_legend import SmartLegendExtension
from .subsuperscript import SubSuperscriptExtension
from .tables import TableExtension
from .title_anchor import TitleAnchorExtension
from .urlize import UrlizeExtension
from .video import VideoExtension


class ZdsExtension(Extension):
    """ Add various extensions to Markdown class."""

    def __init__(self, *args, **kwargs):
        self.config = {
            'inline': [False, ''],
            'emoticons': [{}, ''],
            'js_support': [False, ''],
            'ping_url': [None, ''],
            'marker_key': ["", 'Unique key for the extract used in reference elements'],
            'enable_titles': [False, ''],
        }

        super(ZdsExtension, self).__init__(*args, **kwargs)

    def _create_common_extension(self):
        # create extensions :
        sub_ext = SubSuperscriptExtension()  # Sub and Superscript support
        del_ext = DelExtension()  # Del support
        urlize_ext = UrlizeExtension()  # Autolink support
        typo_ext = FrenchTypographyExtension()  # French typography
        return [sub_ext,  # Subscript support
                del_ext,  # Del support
                urlize_ext,  # Autolink support
                typo_ext]

    def _create_non_inline_extension(self):
        mathjax_ext = MathJaxExtension()  # MathJax support
        kbd_ext = KbdExtension()  # Keyboard support
        emo_ext = EmoticonExtension(emoticons=self.emoticons)  # smileys support
        customblock_ext = CustomBlockExtension(classes={
            "s(ecret)?": "spoiler",
            "i(nformation)?": "information ico-after",
            "q(uestion)?": "question ico-after",
            "a(ttention)?": "warning ico-after",
            "e(rreur)?": "error ico-after",
        })  # CustomBlock support
        align_ext = AlignExtension()  # Right align and center support
        video_ext = VideoExtension(js_support=self.js_support)  # Video support

        gridtable_ext = GridTableExtension()  # Grid Table support
        comment_ext = CommentsExtension(start_tag="<--COMMENT", end_tag="COMMENT-->")  # Comment support
        legend_ext = SmartLegendExtension()  # Smart Legend support
        dheader_ext = DownHeaderExtension(offset=2)  # Offset header support
        ping_ext = PingExtension(ping_url=self.ping_url)  # Ping support

        exts = [AbbrExtension(),  # Abbreviation support, included in python-markdown
                FootnoteExtension(unique_prefix=self.marker_key),
                # Footnotes support, included in python-markdown
                TableExtension(),  # Tables support, included in python-markdown
                # Extended syntaxe for code block support, included in python-markdown
                CodeHiliteExtension(linenums=True, guess_lang=False),
                customblock_ext,  # CustomBlock support
                kbd_ext,  # Kbd support
                emo_ext,  # Smileys support
                video_ext,  # Video support
                gridtable_ext,  # Grid tables support
                align_ext,  # Right align and center support
                dheader_ext,  # Down Header support
                mathjax_ext,  # Mathjax support
                FencedCodeExtension(),
                comment_ext,  # Comment support
                legend_ext,  # Legend support
                ping_ext,  # Ping support
                ]
        if self.enable_titles:
            title_anchor_ext = TitleAnchorExtension(link_position="after", marker_key=self.marker_key)
            exts.append(title_anchor_ext)
        return exts

    def extendMarkdown(self, md, md_globals):
        """ Register extension instances. """
        config = self.getConfigs()
        self.inline = config.get("inline", True)
        self.emoticons = config.get("emoticons", {})
        self.js_support = config.get("js_support", False)
        self.ping_url = config.get('ping_url', None)
        if self.ping_url is None:
            self.ping_url = lambda _: None
        self.marker_key = config.get("marker_key", "")
        self.enable_titles = config.get("enable_titles", True)

        md.inline = self.inline

        # Define used ext
        exts = self._create_common_extension()

        if not self.inline:
            exts.extend(self._create_non_inline_extension())

        md.registerExtensions(exts, {})
        if self.inline:
            md.inlinePatterns.pop("image_link")
            md.inlinePatterns.pop("image_reference")
            md.inlinePatterns.pop("reference")
            md.inlinePatterns.pop("short_reference")
            md.inlinePatterns.pop("linebreak")


def makeExtension(*args, **kwargs):
    return ZdsExtension(*args, **kwargs)
