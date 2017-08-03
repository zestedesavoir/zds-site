from django import template
from django.conf import settings


register = template.Library()


@register.filter('remove_url_protocole')
def remove_url_protocole(input_url):
    """
    make every image url pointing to this website protocol independant so that https is not broken
    """
    if settings.ZDS_APP['site']['dns'] in input_url or settings.ZDS_APP['site']['url'] in input_url:
        return input_url.replace('http:/', 'https:/')\
                        .replace('https://' + settings.ZDS_APP['site']['dns'], '')\
                        .replace(settings.ZDS_APP['site']['url'], '')
    return input_url
