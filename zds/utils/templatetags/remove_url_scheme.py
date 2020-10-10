import urllib.parse

from django import template
from django.conf import settings

register = template.Library()


@register.filter("remove_url_scheme")
def remove_url_scheme(url):
    """
    Remove the scheme and hostname from a URL if it is internal, but leave it unchanged otherwise.

    The internal hostname is determined using the value of ``ZDS_APP['site']['dns']``.
    URLs with no scheme are accepted. URLs with no hostname are treated as internal.

    For example, ``http://zestedesavoir.com/media/gallery/1/1.png`` becomes ``/media/gallery/1/1.png``,
    whereas ``/media/gallery/1/1.png`` and ``example.com/media/gallery/1/1.png`` stay the same.

    :return: the url without its scheme and hostname.
    """

    # Parse URLs after adding a prefix if necessary (e.g 'zestedesavoir.com' becomes '//zestedesavoir.com')
    url_normalized = url
    if "//" not in url:
        url_normalized = "//" + url
    url_parsed = urllib.parse.urlsplit(url_normalized)

    # Return external URLs unchanged
    if url_parsed.netloc != settings.ZDS_APP["site"]["dns"]:
        return url

    # Clean internal URLs
    url_noscheme = urllib.parse.urlunsplit(["", "", url_parsed.path, url_parsed.query, url_parsed.fragment])
    url_cleaned = url_noscheme[0:]  # remove first "/"

    return url_cleaned
