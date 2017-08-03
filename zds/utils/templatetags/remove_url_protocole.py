from django import template
from django.conf.settings import ZDS_APP


register = template.Library()


@register.filter('remove_url_protocole')
def remove_url_protocole(input_url):
    """
    make every image url pointing to this website protocol independant so that https is not broken
    """
    if ZDS_APP['site']['dns'] in input_url or ZDS_APP['site']['url'] in input_url:
        return input_url.replace('http:/', 'https:/')\
                        .replace('https://' + ZDS_APP['site']['dns'], '')\
                        .replace(ZDS_APP['site']['url'], '')
    return input_url
