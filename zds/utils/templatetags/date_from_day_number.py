from datetime import date, timedelta

from django import template

register = template.Library()

# TODO test me !
@register.simple_tag
def date_from_day_number(day_number):
    today = date.today()
    return today - timedelta(days=day_number)

