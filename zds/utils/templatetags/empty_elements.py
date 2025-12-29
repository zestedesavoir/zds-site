from django import template
from django.http import QueryDict
from django.urls import reverse

register = template.Library()


@register.filter(name="empty_dict")
def empty_dict(_):
    return QueryDict()


@register.filter(name="empty_list")
def empty_list(_):
    return []
