from django import template
from django.utils.translation import ugettext_lazy as _

register = template.Library()


@register.simple_tag
def joinby(values, separator=', ', same_final_separator=False):
    """
    Returns a human readable list (of type string) of values separated
    by a string definable with 'separator' (commas default, excepted
    the last preceded by "et") from an iterable.
    Set 'same_final_separator' to True to make the last also preceded
    by the same separator.
    """
    if not values:
        return ''
    if len(values) == 1:
        return str(values[0])
    if same_final_separator:
        final_sep = separator
    else:
        final_sep = _(' et ')
    return separator.join(map(str, values[:len(values) - 1])) + (
        final_sep + str(values.last())
    )
