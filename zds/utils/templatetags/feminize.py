# -*- coding: utf-8 -*-

from django import template
from django.utils.translation import ugettext_lazy as _

register = template.Library()
articles = {
    _('le'): _('la'),
    _('un'): _('une'),
    _('Nouveau'): _('Nouvelle'),
    _('Ce'): _('Cette')
}

words = {
    u'commentaire': False,
    u'partie': True,
    u'chapitre': False,
    u'section': True
}


@register.filter(name='feminize')
def feminize(article, word):
    if article in articles and word.lower() in words:
        if words[word.lower()]:
            return articles[article]

    return article
