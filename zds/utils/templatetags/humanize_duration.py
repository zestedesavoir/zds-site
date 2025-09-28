import logging
import numbers
from collections.abc import Iterable, Iterator
from typing import List, Tuple

from django import template
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

logger = logging.getLogger(__file__)
register = template.Library()


@register.filter
def humanize_duration(duration_min: int) -> str:
    """
    Display a human-readable duration.
    The granularity gets larger as the value gets larger to avoid meaningless precision.

    See the unit tests for examples of results.
    """
    if not isinstance(duration_min, int):
        logger.warning("Invalid duration %s", duration_min)
        return humanize_duration(0)
    duration_min = max(duration_min, 0)  # to avoid surprises with modulo operations
    truncated_value = _truncate_duration(
        duration_min,
        bounds=[600, 120, 60, 30, 15],
        precisions=[60, 30, 15, 10, 5],
    )
    hours, minutes = _minutes_to_hours_and_minutes(truncated_value)
    return _display_hours_and_minutes(hours, minutes)


def _truncate_duration(duration: int, bounds: Iterable[int], precisions: Iterable[int]) -> int:
    """
    Truncate a duration to lower its precision.
    Precisions are given for a set of intervals delimited by the given lower bounds.
    The duration, precisions and bounds are expressed in the same unit (e.g. minutes).
    """
    for bound, precision in zip(bounds, precisions):
        if duration >= bound:
            return duration - (duration % precision)
    return duration


def _minutes_to_hours_and_minutes(duration_min: int) -> tuple[int, int]:
    """
    Convert a duration expressed in minutes to a duration expressed in hours and minutes.
    `duration_min` shall be positive to ensure a correct behavior.
    """
    minutes_per_hour = 60
    hours, minutes = divmod(duration_min, minutes_per_hour)
    return hours, minutes


def _display_hours_and_minutes(hours: int, minutes: int) -> str:
    """Display a human-readable duration given in hours and minutes."""

    minutes_fragment = ngettext("1 minute", "{minutes} minutes", minutes).format(minutes=minutes)
    hours_fragment = ngettext("1 heure", "{hours} heures", hours).format(hours=hours)

    if hours == 0 and minutes == 0:
        return _("moins d'une minute")
    elif hours == 0:
        return minutes_fragment
    elif minutes == 0:
        return hours_fragment
    else:
        return _("{hours} et {minutes}").format(hours=hours_fragment, minutes=minutes_fragment)
