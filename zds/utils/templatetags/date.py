from datetime import datetime, timedelta

from django import template
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.defaultfilters import date
from django.utils.timezone import get_default_timezone
from django.utils.translation import ugettext_lazy as _

register = template.Library()

"""
Define a filter to format date.
"""

# Date formatting constants

__DATE_FMT_FUTUR = _('Dans le futur')
__ABS_DATE_FMT_SMALL = _(r'd/m/y à H\hi')       # Small format
__ABS_DATE_FMT_NORMAL = _(r'l d F Y à H\hi')    # Normal format
__ABS_HUMAN_TIME_FMT = _('%d %b %Y, %H:%M:%S')


def date_formatter(value, tooltip, small):
    """
    Format a date to an human readable string.

    :param value: Date to format.
    :param bool tooltip: if `True`, format date to a tooltip label.
    :param bool small: if `True`, create a shorter string.
    :return:
    """
    if not isinstance(value, datetime):
        return value

    if getattr(value, 'tzinfo', None):
        now = datetime.now(get_default_timezone())
    else:
        now = datetime.now()
    now = now - timedelta(microseconds=now.microsecond)

    if value > now:
        return __DATE_FMT_FUTUR
    else:
        delta = now - value
        # Natural time for today, absolute date after.
        # Reverse if in tooltip
        if (delta.days == 0) != tooltip:
            return naturaltime(value)
        else:
            return date(value, __ABS_DATE_FMT_SMALL if small else __ABS_DATE_FMT_NORMAL)


@register.filter
def format_date(value, small=False):
    """Format a date to an human readable string."""
    return date_formatter(value, tooltip=False, small=small)


@register.filter
def tooltip_date(value):
    """Format a date to an human readable string. To be used in tooltip."""
    return date_formatter(value, tooltip=True, small=False)


@register.filter
def humane_time(timestamp):
    """Render time (number of second from epoch) to an human readable string"""
    return format_date(datetime.fromtimestamp(timestamp))


@register.filter
def from_elasticsearch_date(value):
    try:
        date = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        date = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
    return date
