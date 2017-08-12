from django import template
from django.conf import settings
from six.moves import urllib_parse as urlparse

register = template.Library()


@register.filter('remove_url_scheme')
def remove_url_scheme(input_url):
    """
    make every image url pointing to this website protocol independant so that if we use https, we are sure
    that all our media are served with this protocol.

    .. notice::

        this also removes the ``settings.ZDS_APP['site']['dns']`` from the url.

    :return: the url without its scheme, e.g. ``http://zestedesavoir.com/media/gallery/1/1.png`` becomes
    ``/media/gallery/1/1.png``

    """

    schemeless_url = input_url[len(urlparse.urlparse(input_url).scheme):]
    schemeless_url = schemeless_url[len('://'):] if schemeless_url.startswith('://') else schemeless_url
    if schemeless_url.startswith(settings.ZDS_APP['site']['dns']):
        return schemeless_url[len(settings.ZDS_APP['site']['dns']):]
    return input_url
