from django import template
from zds.settings import ZDS_APP


register = template.Library()


CONVERT_VALUES = ((1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
                  (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'),
                  (4, 'IV'), (1, 'I'))


@register.filter('remove_url_protocole')
def remove_url_protocole(input_url):
    """
    make every image url pointing to this website protocol independant so that https is not broken
    """
    if ZDS_APP["site"]["dns"] in input_url:
        return input_url.replace("http:/", "https:/").replace("https://" + ZDS_APP["site"]["dns"], "")
    return input_url
