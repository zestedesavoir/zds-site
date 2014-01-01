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
                                'codehilite(force_linenos=True)',
							  ])
        .encode('utf-8')))
