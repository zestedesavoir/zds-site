from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag
def joinby(values, separator=", ", final_separator=_(" et ")):
    """
    Returns a human readable list (of type string) of values separated
    by a string definable with 'separator' (commas default) from an
    iterable. Use 'final_separator' to define another separator
    for the last value (" et " default).
    """
    if not values:
        return ""
    # Allows to pass a queryset (instead of a list of strings)
    # to the function.
    values = [str(v) for v in values]
    if len(values) == 1:
        return values[0]
    if separator == final_separator:
        return separator.join(values)
    else:
        return separator.join(values[:-1]) + str(final_separator) + values[-1]
