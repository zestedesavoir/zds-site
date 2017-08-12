from django import template
from django.conf import settings


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
    if settings.ZDS_APP['site']['dns'] in input_url or settings.ZDS_APP['site']['url'] in input_url:
        return input_url.replace('http:/', 'https:/')\
                        .replace('https://' + settings.ZDS_APP['site']['dns'], '')\
                        .replace(settings.ZDS_APP['site']['url'], '')
    return input_url
