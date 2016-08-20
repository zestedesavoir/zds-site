# coding: utf-8
import math
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
    association = ["icon-really-quick", "icon-quick", "icon-mid", "icon-slow", "icon-mid-slow", "icon-really-slow"]
    try:
        # as log(x) is positive if x >= 1, let's use log(max(time, 1.0))
        index = int(math.floor(math.log(max(nb_word_to_time(nb_word), 1.0))))
        return association[max(index, len(association) - 1)]
    except (IndexError, ValueError):
        return association[-1]


@register.filter("nb_word_to_time")
def nb_word_to_time(nb_word):
    return (nb_word + 212) / 213.0  # HuGo reading time trick
