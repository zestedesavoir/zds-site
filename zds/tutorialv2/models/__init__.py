# coding: utf-8

from django.utils.translation import ugettext_lazy as _

TYPE_CHOICES = (
    ('TUTORIAL', 'Tutoriel'),
    ('ARTICLE', 'Article'),
)

TYPE_CHOICES_DICT = dict(TYPE_CHOICES)

STATUS_CHOICES = (
    ('PENDING', _('En attente d\'un validateur')),
    ('PENDING_V', _('En cours de validation')),
    ('ACCEPT', _('Publié')),
    ('REJECT', _('Rejeté')),
    ('CANCEL', _('Annulé'))
)
