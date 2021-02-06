from datetime import date, datetime, timedelta

from django import template

register = template.Library()


# TODO test me !
@register.filter
def datedelta_from_day(day_delta, date_from=None):
    if not date_from:
        reference = date.today()
    else:
        reference = datetime.strptime(date_from, "%Y-%m-%d").date()
    return reference + timedelta(days=day_delta)
