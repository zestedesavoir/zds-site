# coding: utf-8

from django.db import models
from django.utils.translation import ugettext_lazy as _

from zds.member.models import Profile
from zds.news.managers import NewsManager, MessageNewsManager


class News(models.Model):
    class Meta:
        verbose_name = _(u'Une')
        verbose_name_plural = _(u'Unes')

    title = models.CharField(_(u'Titre'), max_length=80)
    type = models.CharField(_(u'Type'), max_length=80)
    authors = models.ManyToManyField(Profile, verbose_name=_(u'Auteurs'), db_index=True)
    image_url = models.CharField(
        _(u'URL de l\'image à la une'), max_length=128, null=False, blank=False
    )
    url = models.CharField(
        _(u'URL de la une'), max_length=128, null=False, blank=False
    )
    pubdate = models.DateTimeField(_(u'Date de publication'), blank=True, null=False, db_index=True)

    objects = NewsManager()

    def __unicode__(self):
        """Textual form of a news."""
        return self.title


class MessageNews(models.Model):
    class Meta:
        verbose_name = _(u'Nouveau')
        verbose_name_plural = _(u'Nouveaux')

    message = models.CharField(u'Message', max_length=255)
    url = models.CharField(_(u'URL du message'), max_length=128, null=False, blank=False)
    objects = MessageNewsManager()

    def __unicode__(self):
        """Textual form of a news."""
        return self.message
