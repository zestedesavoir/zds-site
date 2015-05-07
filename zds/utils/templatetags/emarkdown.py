# coding: utf-8

import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from markdown import Markdown
from markdown.extensions.zds import ZdsExtension

from zds.utils.templatetags.smileysDef import smileys

register = template.Library()

"""
Markdown related filters.
"""

# Constant strings
__MD_ERROR_PARSING = _(u'Une erreur est survenue dans la génération de texte Markdown. Veuillez rapporter le bug.')


def get_markdown_instance(inline=False, js_support=False):
    """
    Provide a pre-configured markdown parser.

    :param bool inline: If `True`, configure parser to parse only inline content.
    :return: A ZMarkdown parser.
    """
    zdsext = ZdsExtension(inline=inline, emoticons=smileys, js_support=js_support)
    # Generate parser
    md = Markdown(
        extensions=(zdsext,),
        safe_mode='escape',       # Protect use of html by escape it
        inline=inline,            # Parse only inline content.
        enable_attributes=False,  # Disable the conversion of attributes.
                                  # This could potentially allow an untrusted user to inject JavaScript into documents.
        tab_length=4,             # Length of tabs in the source (default value).
        output_format='html5',    # HTML5 output (default value).
        smart_emphasis=True,      # Enable smart emphasis for underscore syntax
        lazy_ol=True,             # Enable smart ordered list start support
    )

    return md


def render_markdown(text, inline=False, js_support=False):
    """
    Render a markdown text to html.

    :param str text: Text to render.
    :param bool inline: If `True`, parse only inline content.
    :param bool js_support: Enable JS in generated html.
    :return: Equivalent html string.
    :rtype: str
    """
    return get_markdown_instance(inline=inline, js_support=js_support).convert(text).encode('utf-8').strip()


@register.filter(needs_autoescape=False)
def emarkdown(text, js=''):
    """
    Filter markdown text and render it to html.

    :param str text: Text to render.
    :return: Equivalent html string.
    :rtype: str
    """
    is_js = (js == 'js')
    try:
        return mark_safe(render_markdown(text, inline=False, js_support=is_js))
    except:
        return mark_safe(u'<div class="error ico-after"><p>{}</p></div>'.format(__MD_ERROR_PARSING))


@register.filter(needs_autoescape=False)
def emarkdown_inline(text):
    """
    Filter markdown text and render it to html. Only inline elements will be parsed.

    :param str text: Text to render.
    :return: Equivalent html string.
    :rtype: str
    """

    try:
        return mark_safe(render_markdown(text, inline=True))
    except:
        return mark_safe(u'<p>{}</p>'.format(__MD_ERROR_PARSING))


def sub_hd(match, count):
    """Replace header shifted."""
    st = match.group(1)
    lvl = match.group('level')
    hd = match.group('header')
    end = match.group(4)

    new_content = st + '#' * count + lvl + hd + end

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
