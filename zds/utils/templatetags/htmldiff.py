# coding: utf-8

from difflib import HtmlDiff
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.simple_tag
def htmldiff(string1, string2):
    txt1 = string1.decode('utf-8').splitlines()
    txt2 = string2.decode('utf-8').splitlines()

    diff = HtmlDiff(tabsize=4, wrapcolumn=80)
    result = diff.make_table(txt1, txt2, context=True, numlines=2)

    if u'<td>&nbsp;No Differences Found&nbsp;</td>' in result:
        return _(u'<p>Pas de changements.</p>')
    else:
        return format_html('<div class="diff_delta">{}</div>', mark_safe(result))
