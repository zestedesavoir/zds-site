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
MAX_ATTEMPTS = 3
MD_PARSING_ERROR = _('Une erreur est survenue dans la génération de texte Markdown. Veuillez rapporter le bug.')


def _render_markdown_once(md_input, **kwargs):
    """
    Returns None on error (error details are logged). No retry mechanism.

    """
    def log_args():
        logger.error('md_input: {!r}'.format(md_input))
        logger.error('kwargs: {!r}'.format(kwargs))

    inline = kwargs.get('inline', False) is True
    to_latex = kwargs.get('to_latex', False) is True
    to_latex_document = kwargs.get('to_latex_document', False) is True

    if settings.ZDS_APP['zmd']['disable_pings'] is True:
        kwargs['disable_ping'] = True

    endpoint = '/html'
    if to_latex:
        endpoint = '/latex'
    if to_latex_document:
        endpoint = '/latex-document'

    try:
        response = post('{}{}'.format(settings.ZDS_APP['zmd']['server'], endpoint), json={
            'opts': kwargs,
            'md': str(md_input),
        }, timeout=10)
    except requests.HTTPError:
        logger.exception('An HTTP error happened, markdown rendering failed')
        log_args()
        return None

    if response.status_code != 200:
        logger.error('The markdown server replied with status {} (expected 200)'.format(response.status_code))
        log_args()
        return None

    try:
        content, metadata = response.json()
        content = content.strip()
        if inline:
            content = content.replace('</p>\n', '\n\n').replace('\n<p>', '\n')
        return mark_safe(content), metadata
    except:  # noqa
        logger.exception('Unexpected exception raised')
        log_args()
        return None


def render_markdown(md_input, **kwargs):
    """Render a markdown string.

    Returns a tuple ``(rendered_content, metadata)``, where
    ``rendered_content`` is a string and ``metadata`` is a dict.

    Handles errors gracefully by returning an user-friendly HTML
    string which explains that the Markdown rendering has failed
    (without any technical details).

    """
    result = _render_markdown_once(md_input, **kwargs)
    if result is not None:
        # Success!
        return result

    # Oops, something went wrong

    attempts = kwargs.get('attempts', 0)
    inline = kwargs.get('inline', False) is True

    if attempts < MAX_ATTEMPTS:
        if not kwargs:
            kwargs = dict()
        return render_markdown(md_input, **dict(kwargs, attempts=attempts + 1))

    logger.error('Max attempt count reached, giving up')
    logger.error('md_input: {!r}'.format(md_input))
    logger.error('kwargs: {!r}'.format(kwargs))

    # FIXME: This cannot work with LaTeX.
    if inline:
        return mark_safe('<p>{}</p>'.format(MD_PARSING_ERROR)), {}
    else:
        return mark_safe('<div class="error ico-after"><p>{}</p></div>'.format(MD_PARSING_ERROR)), {}


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
    return content or ''


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
    return re.sub(r'(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)', lambda t: sub_hd(t, count), text)


@register.filter('shift_heading_1')
def shift_heading_1(text):
    return shift_heading(text, 1)


@register.filter('shift_heading_2')
def shift_heading_2(text):
    return shift_heading(text, 2)


@register.filter('shift_heading_3')
def shift_heading_3(text):
    return shift_heading(text, 3)
