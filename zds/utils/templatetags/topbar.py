# coding: utf-8

from django import template

from zds.forum.models import Category as fCategory
from zds.utils.models import Category as Category


register = template.Library()


@register.filter('top_categories')
def top_categories(user):
    categories = fCategory.objects.order_by('position').all()

    return categories


@register.filter('auth_forums')
def auth_forums(forums, user):
    auth = []
    for forum in forums:
        if forum.can_read(user):
            auth.append(forum)

    return auth


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)


@register.filter('top_categories_tuto')
def top_categories_tuto(user):
    categories = Category.objects.all()

    return categories
