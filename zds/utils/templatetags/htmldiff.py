# coding: utf-8

from difflib import HtmlDiff
from django import template


register = template.Library()


@register.simple_tag
def htmldiff(string1, string2):
    txt1 = string1.splitlines()
    txt2 = string2.splitlines()

    diff = HtmlDiff(tabsize=4, wrapcolumn=80)
    result = diff.make_table(txt1, txt2, context=True, numlines=2)

    return '<div class="diff_delta">' + result + '</div>'
