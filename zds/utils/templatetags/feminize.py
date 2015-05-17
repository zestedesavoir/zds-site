# -*- coding: utf-8 -*-

from django import template
from django.utils.translation import ugettext_lazy as _

register = template.Library()
articles = {
    "le": "la",
    "un": "une",
    "Nouveau": "Nouvelle",
    "Ce": "Cette"
}

words = {
    u"réaction": True,
    u"partie": True,
    u"chapitre": False,
    u"section": True
}


@register.filter(name='feminize')
def feminize(article, word):
    if article in articles and word.lower() in words:
        if words[word.lower()]:
            return articles[article]

    return _(article)
