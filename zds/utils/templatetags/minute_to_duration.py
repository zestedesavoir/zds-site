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
    if value <= 0:
        return ''
    # Rounds value to avoid "1 hour, 2 minutes".
    if 55 <= value <= 65:
        value = 60
    elif value > 65:
        value = value - (value % 15)

    min_in_hour = 60
    hours_in_day = 24
    min_in_day = min_in_hour * hours_in_day

    if value < min_in_day & value % min_in_hour == 0:
        value /= min_in_hour

        if value == 1:
            return "1 heure"
        else:
            return f"{value} heures"
    
    if value < min_in_day & value % min_in_hour != 0:
        hours = value // min_in_hour
        minutes = value % min_in_hour
        
        if hours == 1:
            if minutes == 1:
                return "1 heure et 1 minute"
            else:
                return f"1 heure et {minutes} minutes"
        
        else:
            if minutes == 1:
                return f"{hours} heures et 1 minute"
            else:
                return f"{hours} heures et {minutes} minutes"

    if value > min_in_day:
        value //= min_in_hour
        return f"{value} heures"