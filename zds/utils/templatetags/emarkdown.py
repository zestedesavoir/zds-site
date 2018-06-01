import re
import json
import logging
from requests import post, HTTPError

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

FORMAT_ENDPOINTS = {
    'html': '/html',
    'texfile': '/latex-document',
    'epub': '/epub',
    'tex': '/latex',
}


def _render_markdown_once(md_input, *, output_format='html', **kwargs):
    """
    Returns None on error (error details are logged). No retry mechanism.
    """
    def log_args():
        logger.error('md_input: {!r}'.format(md_input))
        logger.error('kwargs: {!r}'.format(kwargs))

    inline = kwargs.get('inline', False) is True

    if settings.ZDS_APP['zmd']['disable_pings'] is True:
        kwargs['disable_ping'] = True

    endpoint = FORMAT_ENDPOINTS[output_format]

    try:
        response = post('{}{}'.format(settings.ZDS_APP['zmd']['server'], endpoint), json={
            'opts': kwargs,
            'md': str(md_input),
        }, timeout=10)
    except HTTPError:
        logger.exception('An HTTP error happened, markdown rendering failed')
        log_args()
        return '', {}, []

    if response.status_code == 413:
        return '', {}, [{'message': str(_('Texte trop volumineux.'))}]

    if response.status_code != 200:
        logger.error('The markdown server replied with status {} (expected 200)'.format(response.status_code))
        log_args()
        return '', {}, []

    try:
        content, metadata, messages = response.json()
        logger.debug('Result %s, %s, %s', content, metadata, messages)
        if messages:
            logger.error('Markdown errors %s', json.dumps(messages))
        content = content.strip()
        if inline:
            content = content.replace('</p>\n', '\n\n').replace('\n<p>', '\n')
        return mark_safe(content), metadata, messages
    except:  # noqa
        logger.exception('Unexpected exception raised')
        log_args()
        return '', {}, []


def render_markdown(md_input, *, on_error=None, **kwargs):
    """Render a markdown string.

    Returns a tuple ``(rendered_content, metadata)``, where
    ``rendered_content`` is a string and ``metadata`` is a dict.

    Handles errors gracefully by returning an user-friendly HTML
    string which explains that the Markdown rendering has failed
    (without any technical details).

    """
    content, metadata, messages = _render_markdown_once(md_input, **kwargs)
    if messages and on_error:
        on_error([m['message'] for m in messages])
    if content is not None:
        # Success!
        return content, metadata, messages

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
        return mark_safe('<p>{}</p>'.format(json.dumps(messages))), metadata, []
    else:
        return mark_safe('<div class="error ico-after"><p>{}</p></div>'.format(json.dumps(messages))), metadata, []


@register.filter(name='epub_markdown', needs_autoescape=False)
def epub_markdown(md_input, image_directory):
    return emarkdown(md_input, output_format='epub', images_download_dir=image_directory,
                     local_url_to_local_path=[settings.MEDIA_URL + '/galleries/[0-9]+', image_directory])


@register.filter(needs_autoescape=False)
@stringfilter
def emarkdown(md_input, use_jsfiddle='', **kwargs):
    """
    :param str md_input: Markdown string.
    :return: HTML string.
    :rtype: str
    """
    disable_jsfiddle = (use_jsfiddle != 'js')

    content, metadata, messages = render_markdown(
        md_input,
        on_error=lambda m: logger.error('Markdown errors %s', str(m)),
        **dict(kwargs, disable_jsfiddle=disable_jsfiddle))

    return content or ''


@register.filter(needs_autoescape=False)
@stringfilter
def emarkdown_preview(md_input, use_jsfiddle='', **kwargs):
    """
    Filter markdown string and render it to html.

    :param str md_input: Markdown string.
    :return: HTML string.
    :rtype: str
    """
    disable_jsfiddle = (use_jsfiddle != 'js')

    content, metadata, messages = render_markdown(
        md_input,
        **dict(kwargs, disable_jsfiddle=disable_jsfiddle))

    if messages:
        content = _('</div><div class="preview-error"><strong>Erreur du serveur Markdown:</strong>\n{}'
                    .format('<br>- '.join([m['message'] for m in messages])))
        content = mark_safe(content)

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
    rendered = emarkdown(text, inline=True)
    return rendered


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
