from django import template
from django.template import defaultfilters as filters
from django.utils.translation import ugettext as _
import datetime

register = template.Library()


# TODO add unit test
@register.filter('seconds_to_duration')
def seconds_to_duration(value):
    """
    Display a human-readable reading-time (or any other duration)
    from a duration in seconds.
    """
    now = datetime.datetime.now()
    if value <= 0:
        return ''

    duration = datetime.timedelta(seconds=value)
    return str(duration)
