# coding: utf-8

import re

from django.conf import settings
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from zmarkdown import ZMarkdown
from zmarkdown.extensions.zds import ZdsExtension

from zds.utils.templatetags.smileysDef import smileys

register = template.Library()

"""
Markdown related filters.
"""

# Constant strings
__MD_ERROR_PARSING = _(u'Une erreur est survenue dans la génération de texte Markdown. Veuillez rapporter le bug.')


def get_markdown_instance(inline=False, js_support=False, ping_url=None):
    """
    Provide a pre-configured markdown parser.

    :param bool inline: If `True`, configure parser to parse only inline content.
    :return: A ZMarkdown parser.
    """
    if not settings.ZDS_APP['comment']['enable_pings']:
        ping_url = None
    zdsext = ZdsExtension(inline=inline, emoticons=smileys, js_support=js_support, ping_url=ping_url)
    # Generate parser
    markdown = ZMarkdown(
        extensions=(zdsext,),
        inline=inline,            # Parse only inline content.
    )

    return markdown


def render_markdown(markdown, text, inline=False):
    """
    Render a markdown text to html.

    :param markdown: Python-ZMarkdown object.
    :param str text: Text to render.
    :param bool inline: If `True`, parse only inline content.
    :return: Equivalent html string.
    :rtype: str
    """
    try:
        return mark_safe(markdown.convert(text).encode('utf-8').strip())
    except:
        if inline:
            return mark_safe(u'<p>{}</p>'.format(__MD_ERROR_PARSING))
        else:
            return mark_safe(u'<div class="error ico-after"><p>{}</p></div>'.format(__MD_ERROR_PARSING))


@register.filter(needs_autoescape=False)
def emarkdown(text, use_jsfiddle='', inline=False):
    """
    Filter markdown text and render it to html.

    :param str text: Text to render.
    :return: Equivalent html string.
    :rtype: str
    """
    md_instance = get_markdown_instance(inline=inline, js_support=(use_jsfiddle == 'js'), ping_url=None)
    return render_markdown(md_instance, text, inline=inline)


@register.filter(needs_autoescape=False)
def emarkdown_inline(text):
    """
    Filter markdown text and render it to html. Only inline elements will be parsed.

    :param str text: Text to render.
    :return: Equivalent html string.
    :rtype: str
    """
    return emarkdown(text, inline=True)


def sub_hd(match, count):
    """Replace header shifted."""
    subt = match.group(1)
    lvl = match.group('level')
    header = match.group('header')
    end = match.group(4)

    new_content = subt + '#' * count + lvl + header + end

    return new_content


def decale_header(text, count):
    """
    Shift header in markdown document.

    :param str text: Text to filter.
    :param int count:
    :return: Filtered text.
    :rtype: str
    """
    return re.sub(r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)', lambda t: sub_hd(t, count), text.encode('utf-8'))


@register.filter('decale_header_1')
def decale_header_1(text):
    return decale_header(text, 1)


@register.filter('decale_header_2')
def decale_header_2(text):
    return decale_header(text, 2)


@register.filter('decale_header_3')
def decale_header_3(text):
    return decale_header(text, 3)
