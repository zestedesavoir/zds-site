# coding: utf-8

import json
import logging
import re
import sys
import zerorpc
from zerorpc.exceptions import RemoteError, TimeoutExpired

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)
register = template.Library()
"""
Markdown related filters.
"""

# Constant strings
MD_PARSING_ERROR = _(u'Une erreur est survenue dans la génération de texte Markdown. Veuillez rapporter le bug.')

markdown_client = zerorpc.Client(heartbeat=5)
markdown_client.connect("tcp://127.0.0.1:24242")


def render_markdown(md_input, **kwargs):
    """
    Render a markdown string.
    """
    inline = kwargs.get('inline', False) is True
    is_latex = kwargs.pop('is_latex', False) is True
    markdown_compiler = markdown_client.toHTML if not is_latex else markdown_client.toLatex
    metadata = {}

    try:
        content, metadata = markdown_compiler(str(md_input), kwargs)
        content = content.encode('utf-8').strip()
        if inline:
            content = content.replace('</p>\n', '\n\n').replace('\n<p>', '\n')
        return mark_safe(content), metadata
    except (RemoteError, TimeoutExpired) as e:
        logger.warn(e)
    except:
        logger.exception("Could not generate markdown")

    disable_ping = kwargs.get('disable_ping', False)
    if not settings.ZDS_APP['comment']['enable_pings']:
        disable_ping = True

    attempts = kwargs.get('attempts', 0)
    if attempts < 3:
        logger.warn("RETRYING")
        if not kwargs:
            kwargs = dict()
        return render_markdown(
            md_input,
            **dict(
                kwargs,
                disable_ping=disable_ping,
                attempts=attempts + 1,
                is_latex=is_latex
            ))

    if inline:
        return mark_safe(u'<p>{}</p>'.format(MD_PARSING_ERROR)), metadata
    else:
        return mark_safe(u'<div class="error ico-after"><p>{}</p></div>'.format(MD_PARSING_ERROR)), metadata


@register.filter(needs_autoescape=False)
@stringfilter
def emarkdown(md_input, use_jsfiddle='', **kwargs):
    """
    Filter markdown string and render it to html.

    :param str md_input: Markdown string.
    :return: HTML string.
    :rtype: str
    """
    disable_jsfiddle = (use_jsfiddle != 'js')

    content, metadata = render_markdown(md_input, **dict(kwargs, disable_jsfiddle=disable_jsfiddle))
    return content


@register.filter(needs_autoescape=False)
@stringfilter
def emarkdown_inline(text):
    """
    Parses inline elements only and renders HTML. Mainly for member signatures.
    Although they are inline elements, pings are disabled.

    :param str text: Markdown string.
    :return: HTML string.
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


def shift_heading(text, count):
    """
    Shift header in markdown document.

    :param str text: Text to filter.
    :param int count:
    :return: Filtered text.
    :rtype: str
    """
    return re.sub(r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)', lambda t: sub_hd(t, count), text.encode('utf-8'))


@register.filter('shift_heading_1')
def shift_heading_1(text):
    return shift_heading(text, 1)


@register.filter('shift_heading_2')
def shift_heading_2(text):
    return shift_heading(text, 2)


@register.filter('shift_heading_3')
def shift_heading_3(text):
    return shift_heading(text, 3)
