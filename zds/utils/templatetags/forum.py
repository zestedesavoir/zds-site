# coding: utf-8

from django import template

register = template.Library()


@register.filter('readable')
def readable(forum, user):
    return forum.can_read(user)
