# coding: utf-8

import bleach
from django import template
from django.utils.safestring import mark_safe
import markdown
import time


register = template.Library()

@register.filter('humane_time')
def humane_time(t, conf={}):
    tp = time.localtime(t)
    return time.strftime("%d %b %Y, %H:%M:%S", tp)

@register.filter(needs_autoescape=False)
def emarkdown(value):
    return mark_safe('<div class="markdown">{0}</div>'.format(
            markdown.markdown(  value, 
                                extensions=[
                                'abbr',                             # Abbreviation support, included in python-markdown
                                'footnotes',                        # Footnotes support, included in python-markdown
                                                                    # Footnotes place marker can be set with the PLACE_MARKER option
                                'tables',                           # Tables support, included in python-markdown
                                'nl2br',                            # Convert new line to br tags support, included in python markdown
                                'fenced_code',                      # Extended syntaxe for code block support, included in python-markdown
                                'codehilite(force_linenos=True)',   # Code hightlight support, with line numbers, included in python-markdwon
							  ])
        .encode('utf-8')))
