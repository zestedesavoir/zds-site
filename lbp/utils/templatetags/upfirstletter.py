# coding: utf-8

from django import template

register = template.Library()


@register.filter()
def upfirstletter(value):
    # This function uses value[0] instead of value[1] because value[0] seems
    # to be empty when used with the humane_date tag.
    first = value[1] if len(value) > 1 else ''
    remaining = value[2:] if len(value) > 2 else ''
    return first.upper() + remaining
