from difflib import HtmlDiff

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag
def htmldiff(string1, string2):
    try:
        txt1 = string1.decode("utf-8").splitlines()
    # string1 is an empty SafeText from template
    except AttributeError:
        txt1 = string1.splitlines()

    try:
        txt2 = string2.decode("utf-8").splitlines()
    except AttributeError:
        txt2 = string2.splitlines()

    diff = HtmlDiff(tabsize=4)
    result = diff.make_table(txt1, txt2, context=True, numlines=2)

    if "No Differences Found" in result:
        return format_html("<p>{}</p>", _("Pas de changements."))
    else:
        # the diff.make_table() replaces all spaces by non-breakable ones, which prevent line breaks:
        r = mark_safe(result.replace('<td nowrap="nowrap">', "<td>").replace("&nbsp;", " "))
        return format_html('<div class="diff_delta">{}</div>', r)
