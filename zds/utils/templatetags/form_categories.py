# coding: utf-8

from django import template

from zds.utils.models import SubCategory


register = template.Library()


@register.filter('order_categories')
def order_categories(choices):
    new_choices = []
    for choice in choices:
        subcat = SubCategory.objects.get(pk=choice[0])
        parent = subcat.get_parent_category()
        ch = {
            'choice': choice,
            'parent': parent.title,
            'order': parent.pk
        }
        new_choices.append(ch)
    return new_choices
