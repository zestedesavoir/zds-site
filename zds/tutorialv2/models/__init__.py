# coding: utf-8

from django.utils.translation import ugettext_lazy as _

TYPE_CHOICES = (
    ('TUTORIAL', 'Tutoriel'),
    ('ARTICLE', 'Article'),
)

TYPE_CHOICES_DICT = dict(TYPE_CHOICES)

STATUS_CHOICES = (
    ('PENDING', _(u'En attente d\'un validateur')),
    ('PENDING_V', _(u'En cours de validation')),
    ('ACCEPT', _(u'Publié')),
    ('REJECT', _(u'Rejeté')),
    ('CANCEL', _(u'Annulé'))
)
