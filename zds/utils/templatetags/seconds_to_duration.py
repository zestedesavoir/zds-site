from django import template
import datetime

register = template.Library()


# TODO add unit test
@register.filter('seconds_to_duration')
def seconds_to_duration(value):
    """
    Display a human-readable reading-time (or any other duration)
    from a duration in seconds.
    """
    if value <= 0:
        return ''

    duration = datetime.timedelta(seconds=value)
    return str(duration)
