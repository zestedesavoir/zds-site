# coding: utf-8
from django import template
from git import *

from zds.forum.models import Category, Forum


register = template.Library()

@register.filter('readable')
def readable(forum, user):
    return forum.can_read(user)