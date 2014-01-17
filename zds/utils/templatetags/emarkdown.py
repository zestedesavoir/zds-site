# coding: utf-8

import bleach
from django import template
from django.utils.safestring import mark_safe
import markdown
import time

#Markdowns customs extensions :
from zds.utils.templatetags.mkd_ext.subsuperscript import SubSuperscriptExtension
from zds.utils.templatetags.mkd_ext.delext import DelExtension
from zds.utils.templatetags.mkd_ext.urlize import UrlizeExtension
from zds.utils.templatetags.mkd_ext.kbd import KbdExtension
from zds.utils.templatetags.mkd_ext.mathjax import MathJaxExtension
from zds.utils.templatetags.mkd_ext.customblock import CustomBlockExtension
from zds.utils.templatetags.mkd_ext.align import AlignExtension
from zds.utils.templatetags.mkd_ext.video import VideoExtension
from zds.utils.templatetags.mkd_ext.preprocessblock import PreprocessBlockExtension
from zds.utils.templatetags.mkd_ext.emoticons import EmoticonExtension
from zds.utils.templatetags.smileysDef import *
from zds.utils.templatetags.mkd_ext.grid_tables import GridTableExtension
from zds.utils.templatetags.mkd_ext.comments import CommentsExtension
from zds.utils.templatetags.mkd_ext.tablelegend import TableLegendExtension
from zds.utils.templatetags.mkd_ext.codelegend import CodeLegendExtension
from zds.utils.templatetags.mkd_ext.smartImg import SmartImgExtension
from zds.utils.templatetags.mkd_ext.headerDec import DownHeaderExtension

sub_ext         = SubSuperscriptExtension() # Sub and Superscript support
del_ext         = DelExtension()            # Del support
urlize_ext      = UrlizeExtension()         # Autolink support
kbd_ext         = KbdExtension()            # Keyboard support
mathjax_ext     = MathJaxExtension()        # MathJax support
customblock_ext = CustomBlockExtension(
    { "s(ecret)?"       : "spoiler",
      "i(nformation)?"  : "information ico-after",
      "q(uestion)?"     : "question ico-after",
      "a(ttention)?"    : "warning ico-after",
      "e(rreur)?"       : "error ico-after",
    })                                      # CustomBlock support
align_ext       = AlignExtension()          # Right align and center support
video_ext       = VideoExtension()          # Video support
preprocess_ext  = PreprocessBlockExtension({"preprocess" : ("fenced_code_block",)}) # Preprocess extension
emo_ext         = EmoticonExtension({"EMOTICONS" : smileys}) # smileys support
gridtable_ext   = GridTableExtension()      # Grid Table support
comment_ext     = CommentsExtension({"START_TAG" : "<--COMMENT", "END_TAG" : "COMMENT-->"}) # Comment support
legend_ext      = TableLegendExtension()    # Table Legend support
legendcode_ext  = CodeLegendExtension()     # Code Legend support
smimg_ext       = SmartImgExtension({"IGNORING_IMG" : smileys.values(), "PARENTS" : ("div", "blockquote")})       # Smart image support
dheader_ext     = DownHeaderExtension({"OFFSET" : 2, }) # Offset header support

register = template.Library()

@register.filter('humane_time')
def humane_time(t, conf={}):
    tp = time.localtime(t)
    return time.strftime("%d %b %Y, %H:%M:%S", tp)

@register.filter(needs_autoescape=False)
def emarkdown(text):
    return mark_safe('<div class="markdown">{0}</div>'.format(
            markdown.markdown(  text, 
                                extensions = [
                                'abbr',                             # Abbreviation support, included in python-markdown
                                'footnotes',                        # Footnotes support, included in python-markdown
                                                                    # Footnotes place marker can be set with the PLACE_MARKER option
                                'tables',                           # Tables support, included in python-markdown
                                'fenced_code',                      # Extended syntaxe for code block support, included in python-markdown
                                'codehilite(linenums=True)',        # Code hightlight support, with line numbers, included in python-markdwon
                                # Externs extensions :
                                sub_ext,                            # Subscript support
                                del_ext,                            # Del support
                                urlize_ext,                         # Autolink support
                                kbd_ext,                            # Kbd support
                                mathjax_ext,                        # Mathjax support
                                customblock_ext,                    # CustomBlock support
                                video_ext,                          # Video support
                                preprocess_ext,                     # Preprocess support
                                emo_ext,                            # Smileys support
                                gridtable_ext,                      # Grid tables support
                                comment_ext,                        # Comment support
                                legend_ext,                         # Legend support
                                legendcode_ext,                     # Legend support
                                smimg_ext,                          # SmartImg support
                                align_ext,                          # Right align and center support
                                dheader_ext,                        # Down Header support
                                'nl2br',                            # Convert new line to br tags support, included in python markdown
                                ],
                                safe_mode           = 'escape',     # Protect use of html by escape it
                                enable_attributes   = False,        # Disable the conversion of attributes.
                                                                    # This could potentially allow an
                                                                    # untrusted user to inject JavaScript
                                                                    # into documents.
                                tab_length          = 4,            # Length of tabs in the source.
                                                                    # This is the default value
                                output_format       = 'html5',      # html5 output
                                                                    # This is the default value
                                smart_emphasis      = True,         # Enable smart emphasis for underscore syntax
                                lazy_ol             = True,         # Enable smart ordered list start support
                              )
        .encode('utf-8')))
