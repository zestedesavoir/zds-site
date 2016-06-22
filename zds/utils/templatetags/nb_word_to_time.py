# coding: utf-8

from django import template
from zds.settings import ZDS_APP
register = template.Library()


@register.filter(name="nb_word_to_icontime")
def nb_word_to_icontime(nb_word):
    """
    Gets the icon for this time to read the content
    :param nb_word:
    :return:
    """
    association = ["icon-15-min", "icon-30-min", "icon-45-min", "icon-60-min", "icon-more-min"]
    try:

        return association[(nb_word / ZDS_APP["content"]["word_per_minute"]) // 15]
    except (IndexError, ValueError):
        return association[-1]


@register.filter("nb_word_to_time")
def nb_word_to_time(nb_word):
    return nb_word // ZDS_APP["content"]["word_per_minute"]