# coding: utf-8

from datetime import timedelta

from django import template
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.defaultfilters import date
from django.utils.datetime_safe import datetime
from django.utils.tzinfo import LocalTimezone


register = template.Library()


def date_formatter(value, tooltip):
    try:
        value = datetime(value.year, value.month, value.day,
                         value.hour, value.minute, value.second)
    except AttributeError:
        return value
    except ValueError:
        return value

    if getattr(value, 'tzinfo', None):
        now = datetime.now(LocalTimezone(value))
    else:
        now = datetime.now()
    now = now - timedelta(0, 0, now.microsecond)
    if value > now:
        return "Dans le futur"
    else:
        delta = now - value
        # Natural time for today, absolute date after.
        # Reverse if in tooltip
        if (delta.days == 0) != tooltip:
            return naturaltime(value)
        else:
            return date(value, 'l d F Y à G\hi')


@register.filter
def format_date(value):
    return date_formatter(value, False)


@register.filter
def tooltip_date(value):
    return date_formatter(value, True)
