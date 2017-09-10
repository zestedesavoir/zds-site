# coding: utf-8

import logging
import re

import requests
from requests import post

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

# Constants
MAX_ATTEMPS = 3
MD_PARSING_ERROR = _(u'Une erreur est survenue dans la génération de texte Markdown. Veuillez rapporter le bug.')


def render_markdown(md_input, **kwargs):
    """
    Render a markdown string.
    """
    attempts = kwargs.get('attempts', 0)
    inline = kwargs.get('inline', False) is True
    to_latex = kwargs.get('to_latex', False) is True
    to_latex_document = kwargs.get('to_latex_document', False) is True

    endpoint = '/html'
    if to_latex:
        endpoint = '/latex'
    if to_latex_document:
        endpoint = '/latex-document'

    metadata = {}

    if settings.ZDS_APP['zmd']['disable_pings'] is True:
        kwargs['disable_ping'] = True

    try:
        response = post('{}{}'.format(settings.ZDS_APP['zmd']['server'], endpoint), json={
            'opts': kwargs,
            'md': str(md_input),
        }, timeout=10)
        content, metadata = response.json()
        content = content.encode('utf-8').strip()
        if inline:
            content = content.replace('</p>\n', '\n\n').replace('\n<p>', '\n')
        return mark_safe(content), metadata
    except (requests.HTTPError, ValueError):
        logger.info('Markdown render failed, attempt {}/{}'.format(attempts, MAX_ATTEMPS), md_input, kwargs)
        logger.exception('Could not generate markdown')
    except:  # noqa
        logger.exception('Unexpected exception raised, attempt {}/{}'.format(attempts, MAX_ATTEMPS), md_input, kwargs)

    if attempts < MAX_ATTEMPS:
        if not kwargs:
            kwargs = dict()
        return render_markdown(md_input, **dict(kwargs, attempts=attempts + 1))

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

    content, _ = render_markdown(md_input, **dict(kwargs, disable_jsfiddle=disable_jsfiddle))
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
