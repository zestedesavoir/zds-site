import json
import logging
import re

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from requests import HTTPError, post

logger = logging.getLogger(__name__)
register = template.Library()
"""
Markdown related filters.
"""

# Constants
MAX_ATTEMPTS = 3
MD_PARSING_ERROR = _("Une erreur est survenue dans la génération de texte Markdown. Veuillez rapporter le bug.")

FORMAT_ENDPOINTS = {
    "html": "/html",
    "texfile": "/latex-document",
    "epub": "/epub",
    "tex": "/latex",
}


def _render_markdown_once(md_input, *, output_format="html", **kwargs):
    """
    Returns None on error (error details are logged). No retry mechanism.
    """

    def log_args():
        logger.error(f"md_input: {md_input!r}")
        logger.error(f"kwargs: {kwargs!r}")

    inline = kwargs.get("inline", False) is True
    full_json = kwargs.pop("full_json", False)

    if settings.ZDS_APP["zmd"]["disable_pings"] is True:
        kwargs["disable_ping"] = True

    endpoint = FORMAT_ENDPOINTS[output_format]

    try:
        timeout = 10
        real_input = str(md_input)
        if output_format.startswith("tex") or full_json:
            # latex may be really long to generate but it is also restrained by server configuration
            timeout = 120
            # use manifest renderer
            real_input = md_input
        response = post(
            "{}{}".format(settings.ZDS_APP["zmd"]["server"], endpoint),
            json={
                "opts": kwargs,
                "md": real_input,
            },
            timeout=timeout,
        )
    except HTTPError:
        logger.exception("An HTTP error happened, markdown rendering failed")
        log_args()
        return "", {}, []

    if response.status_code == 413:
        return "", {}, [{"message": str(_("Texte trop volumineux."))}]

    if response.status_code != 200:
        logger.error(f"The markdown server replied with status {response.status_code} (expected 200)")
        log_args()
        return "", {}, []

    try:
        content, metadata, messages = response.json()
        logger.debug("Result %s, %s, %s", content, metadata, messages)
        if messages:
            logger.error("Markdown errors %s", json.dumps(messages))
        if isinstance(content, str):
            content = content.strip()
        if inline:
            content = content.replace("</p>\n", "\n\n").replace("\n<p>", "\n")
        if full_json:
            return content, metadata, messages
        return mark_safe(content), metadata, messages
    except:  # noqa
        logger.exception("Unexpected exception raised")
        log_args()
        return "", {}, []


def render_markdown(md_input, *, on_error=None, disable_jsfiddle=True, **kwargs):
    """Render a markdown string.

    Returns a tuple ``(rendered_content, metadata)``, where
    ``rendered_content`` is a string and ``metadata`` is a dict.

    Handles errors gracefully by returning an user-friendly HTML
    string which explains that the Markdown rendering has failed
    (without any technical details).

    """
    opts = {"disable_jsfiddle": disable_jsfiddle}
    opts.update(kwargs)
    content, metadata, messages = _render_markdown_once(md_input, **opts)
    if messages and on_error:
        on_error([m["message"] for m in messages])
    if content is not None:
        # Success!
        return content, metadata, messages

    # Oops, something went wrong

    attempts = kwargs.get("attempts", 0)
    inline = kwargs.get("inline", False) is True

    if attempts < MAX_ATTEMPTS:
        if not kwargs:
            kwargs = dict()
        return render_markdown(md_input, **dict(kwargs, attempts=attempts + 1))

    logger.error("Max attempt count reached, giving up")
    logger.error(f"md_input: {md_input!r}")
    logger.error(f"kwargs: {kwargs!r}")

    # FIXME: This cannot work with LaTeX.
    if inline:
        return mark_safe(f"<p>{json.dumps(messages)}</p>"), metadata, []
    else:
        return mark_safe(f'<div class="error ico-after"><p>{json.dumps(messages)}</p></div>'), metadata, []


def render_markdown_stats(md_input, **kwargs):
    """
    Returns contents statistics (words and chars)
    """
    kwargs["stats"] = True
    kwargs["disable_images_download"] = True
    logger.setLevel(logging.INFO)
    content, metadata, messages = _render_markdown_once(md_input, output_format="tex", **kwargs)
    if metadata:
        return metadata.get("stats", {}).get("signs", {})
    return None


@register.filter(name="epub_markdown", needs_autoescape=False)
def epub_markdown(md_input, image_directory):
    media_root = str(settings.MEDIA_ROOT)
    if not media_root.endswith("/"):
        media_root += "/"
    replaced_media_url = settings.MEDIA_URL
    if replaced_media_url.startswith("/"):
        replaced_media_url = replaced_media_url[1:]
    return mark_safe(
        emarkdown(
            md_input,
            output_format="epub",
            images_download_dir=image_directory.absolute,
        )
        .replace('src"/', f'src="{media_root}')
        .replace(f'src="{media_root}{replaced_media_url}', f'src="{media_root}')
    )


@register.filter(needs_autoescape=False)
@stringfilter
def emarkdown(md_input, use_jsfiddle="", **kwargs):
    """
    :param str md_input: Markdown string.
    :return: HTML string.
    :rtype: str
    """
    disable_jsfiddle = use_jsfiddle != "js"
    content, metadata, messages = render_markdown(
        md_input,
        on_error=lambda m: logger.error("Markdown errors %s", str(m)),
        **dict(kwargs, disable_jsfiddle=disable_jsfiddle),
    )
    kwargs.get("metadata", {}).update(metadata)
    return content or ""


@register.filter(needs_autoescape=False)
@stringfilter
def emarkdown_preview(md_input, use_jsfiddle="", **kwargs):
    """
    Filter markdown string and render it to html.

    :param str md_input: Markdown string.
    :return: HTML string.
    :rtype: str
    """
    disable_jsfiddle = use_jsfiddle != "js"

    content, metadata, messages = render_markdown(md_input, **dict(kwargs, disable_jsfiddle=disable_jsfiddle))

    if messages:
        content = _(
            '</div><div class="preview-error"><strong>Erreur du serveur Markdown:</strong>\n{}'.format(
                "<br>- ".join([m["message"] for m in messages])
            )
        )
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
    return mark_safe(rendered.replace("<a href=", '<a rel="nofollow" href='))


def sub_hd(match, count):
    """Replace header shifted."""
    subt = match.group(1)
    lvl = match.group("level")
    header = match.group("header")
    end = match.group(4)

    new_content = subt + "#" * count + lvl + header + end

    return new_content


def shift_heading(text, count):
    """
    Shift header in markdown document.

    :param str text: Text to filter.
    :param int count:
    :return: Filtered text.
    :rtype: str
    """
    text_by_code = re.split("(```|~~~)", text)
    starting_code = None
    for i, element in enumerate(text_by_code):
        if element in ["```", "~~~"] and not starting_code:
            starting_code = element
        elif element == starting_code:
            starting_code = None
        elif starting_code is None:
            text_by_code[i] = re.sub(
                r"(^|\n)(?P<level>#{1,4})(?P<header>.*?)#*(\n|$)", lambda t: sub_hd(t, count), text_by_code[i]
            )

    return "".join(text_by_code)


@register.filter("shift_heading_1")
def shift_heading_1(text):
    return shift_heading(text, 1)


@register.filter("shift_heading_2")
def shift_heading_2(text):
    return shift_heading(text, 2)


@register.filter("shift_heading_3")
def shift_heading_3(text):
    return shift_heading(text, 3)
