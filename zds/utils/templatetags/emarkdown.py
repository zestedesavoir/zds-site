# coding: utf-8

from functools import partial
import re

from django import template
from django.utils.safestring import mark_safe

import markdown
from markdown.extensions.zds import ZdsExtension
from zds.utils.templatetags.smileysDef import smileys

register = template.Library()

"""
Markdown related filters.
"""

def get_markdown_instance(inline=False):
    """
    Provide a pre-configured markdown parser.

    :param bool inline: If `True`, configure parser to parse only inline content.
    :return: A ZMarkdown parser.
    """
    zdsext = ZdsExtension({"inline": inline, "emoticons": smileys})
    # Generate parser
    md = markdown.Markdown(extensions=(zdsext,),
                           safe_mode = 'escape',
                           # Protect use of html by escape it
                           inline = inline,
                           # Parse only inline content.
                           enable_attributes = False,
                           # Disable the conversion of attributes.
                           # This could potentially allow an
                           # untrusted user to inject JavaScript
                           # into documents.
                           tab_length = 4,
                           # Length of tabs in the source.
                           # This is the default value
                           output_format = 'html5',
                           # html5 output
                           # This is the default value
                           smart_emphasis = True,
                           # Enable smart emphasis for underscore syntax
                           lazy_ol = True,
                           # Enable smart ordered list start support
                           )
    return md


@register.filter(needs_autoescape=False)
def emarkdown(text):
    try:
        return mark_safe(
            get_markdown_instance(inline=False).convert(text).encode('utf-8'))

    except:
        return mark_safe(
            u'<div class="error ico-after"><p>Une erreur est survenue '
            u'dans la génération de texte Markdown. Veuillez rapporter le bug</p>')


@register.filter(needs_autoescape=False)
def emarkdown_inline(text):
    return mark_safe(
        get_markdown_instance(
            inline=True).convert(text).encode('utf-8').strip())


def decale_header(text, count):

    def sub_hd(match):
        lvl = match.group('level')
        hd = match.group('header')

        new_content = "#" * count + lvl + hd

        return new_content

    return re.sub(
        r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)',
        sub_hd,
        text.encode("utf-8"))


for i in range(4):
    register.filter('decale_header_{}'.format(i))(partial(decale_header, count=i))
