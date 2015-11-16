# coding: utf-8

from django import template

register = template.Library()


@register.filter("displayable_authors")
def displayable_authors(content, online):
    if online:
        return content.public_version.authors.all()
    return content.authors.all()
