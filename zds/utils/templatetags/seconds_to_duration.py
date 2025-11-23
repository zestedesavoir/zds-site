import datetime

from django import template

register = template.Library()


# https://stackoverflow.com/a/8907269/2226755
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


# TODO add unit test
@register.filter("seconds_to_duration")
def seconds_to_duration(value):
    """
    Display a human-readable reading-time (or any other duration)
    from a duration in seconds.
    """
    if value <= 0:
        return ""

    duration = datetime.timedelta(seconds=value)
    if datetime.timedelta(hours=1) > duration:
        return strfdelta(duration, "{minutes}m{seconds}s")
    else:
        return strfdelta(duration, "{hours}h{minutes}m{seconds}s")
