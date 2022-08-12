from django import template
from django.core.cache import cache


register = template.Library()


@register.filter("topics_sort")
def topics_sort(topics):
    """
    :return: the topics sorted by last update (last updated first)
    """
    return sorted(topics, key=lambda topic: topic.last_update, reverse=True)
