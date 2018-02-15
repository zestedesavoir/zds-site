from django import template
from django.template import defaultfilters as filters
from django.utils.translation import ugettext as _
import datetime

register = template.Library()


@register.filter('minute_to_duration')
def minute_to_duration(value):
    """
    Display a human-readable reading-time (or any other duration)
    from a duration in minutes, with a granularity of 15 minutes.
    """
    now = datetime.datetime.now()
    if value <= 0:
        return ''
    # Rounds value to avoid "1 hour, 2 minutes".
    if 55 <= value <= 65:
        value = 60
    elif value > 65:
        value = value - (value % 15)
    delta = now - datetime.timedelta(minutes=value)
    return filters.timesince(delta).replace(', ', _(' et '))
