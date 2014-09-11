# coding: utf-8

from django import template
from django.utils.safestring import mark_safe
import time
import re

import markdown
from markdown.extensions.zds import ZdsExtension
from zds.utils.templatetags.smileysDef import smileys


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

register = template.Library()


@register.filter('humane_time')
def humane_time(t):
    tp = time.localtime(t)
    return time.strftime("%d %b %Y, %H:%M:%S", tp)


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


def sub_hd1(g):
    lvl = g.group('level')
    hd = g.group('header')
    next = "#" + lvl + hd

    return next


def sub_hd2(g):
    lvl = g.group('level')
    hd = g.group('header')
    next = "#" + lvl + hd

    return next


def sub_hd3(g):
    lvl = g.group('level')
    hd = g.group('header')
    next = "###" + lvl + hd

    return next


@register.filter('decale_header_1')
def decale_header_1(text):
    return re.sub(
        r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)',
        sub_hd1,
        text.encode("utf-8"))


@register.filter('decale_header_2')
def decale_header_2(text):
    return re.sub(
        r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)',
        sub_hd2,
        text.encode("utf-8"))


@register.filter('decale_header_3')
def decale_header_3(text):
    return re.sub(
        r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)',
        sub_hd3,
        text.encode("utf-8"))
