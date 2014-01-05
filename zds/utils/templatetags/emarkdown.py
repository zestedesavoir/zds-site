# coding: utf-8

import bleach
from django import template
from django.utils.safestring import mark_safe
import markdown
import time

#Markdowns customs extensions :
from zds.utils.templatetags.mkd_ext.superscript import SuperscriptExtension
from zds.utils.templatetags.mkd_ext.subscript import SubscriptExtension
from zds.utils.templatetags.mkd_ext.delext import DelExtension
from zds.utils.templatetags.mkd_ext.urlize import UrlizeExtension
from zds.utils.templatetags.mkd_ext.kbd import KbdExtension
from zds.utils.templatetags.mkd_ext.mathjax import MathJaxExtension
from zds.utils.templatetags.mkd_ext.customblock import CustomBlockExtension
from zds.utils.templatetags.mkd_ext.center import CenterExtension
from zds.utils.templatetags.mkd_ext.rightalign import RightAlignExtension
from zds.utils.templatetags.mkd_ext.video import VideoExtension

sup_ext = SuperscriptExtension()            # Superscript support
sub_ext = SubscriptExtension()              # Subscript support
del_ext = DelExtension()                    # Del support
urlize_ext = UrlizeExtension()              # Autolink support
kbd_ext = KbdExtension()                    # Keyboard support
mathjax_ext = MathJaxExtension()            # MathJax support
customblock_ext = CustomBlockExtension()    # CustomBlock support
center_ext = CenterExtension()              # Center support
rightalign_ext = RightAlignExtension()      # CustomBlock support
video_ext = VideoExtension()                # Video support

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
                                'nl2br',                            # Convert new line to br tags support, included in python markdown
                                'fenced_code',                      # Extended syntaxe for code block support, included in python-markdown
                                'codehilite(force_linenos=True)',   # Code hightlight support, with line numbers, included in python-markdwon
                                # Externs extensions :
                                sup_ext,                            # Superscript support
                                sub_ext,                            # Subscript support
                                del_ext,                            # Del support
							    urlize_ext,                         # Autolink support
                                kbd_ext,                            # Kbd support
                                mathjax_ext,                        # Mathjax support
                                customblock_ext,                    # CustomBlock support
                                center_ext,                         # Center support
                                rightalign_ext,                     # Right align support
                                video_ext,                          # Video support
                                ],
                                safe_mode           = 'escape',     # Protect use of html by escape it
                                enable_attributes   = False,        # Disable the conversion of attributes.
                                                                    # This could potentially allow an
                                                                    # untrusted user to inject JavaScript
                                                                    # into documents.
                                tab_length          = 4,            # Length of tabs in the source.
                                                                    # This is the default value
                                output_format       = 'xhtml1',     # Xhtml1 output
                                                                    # This is the default value
                                smart_emphasis      = True,         # Enable smart emphasis for underscore syntax
                                lazy_ol             = True,         # Enable smart ordered list start support
                              )
        .encode('utf-8')))
