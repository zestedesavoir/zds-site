# coding: utf-8

from django.db import models
from django.utils.translation import ugettext_lazy as _

from zds.member.models import Profile
from zds.featured.managers import FeaturedResourceManager, FeaturedMessageManager


class FeaturedResource(models.Model):
    class Meta:
        verbose_name = _(u'Une')
        verbose_name_plural = _(u'Unes')

    title = models.CharField(_(u'Titre'), max_length=80)
    type = models.CharField(_(u'Type'), max_length=80)
    authors = models.ManyToManyField(Profile, verbose_name=_(u'Auteurs'), db_index=True)
    image_url = models.CharField(
        _(u'URL de l\'image à la une'), max_length=2000, null=False, blank=False
    )
    url = models.CharField(
        _(u'URL de la une'), max_length=2000, null=False, blank=False
    )
    pubdate = models.DateTimeField(_(u'Date de publication'), blank=True, null=False, db_index=True)

    objects = FeaturedResourceManager()

    def __unicode__(self):
        """Textual form of a featured resource."""
        return self.title


class FeaturedMessage(models.Model):
    class Meta:
        verbose_name = _(u'Message')
        verbose_name_plural = _(u'Messages')

    hook = models.CharField(_(u'Accroche'), max_length=100, blank=True, null=True)
    message = models.CharField(_(u'Message'), max_length=255, blank=True, null=True)
    url = models.CharField(_(u'URL du message'), max_length=2000, blank=True, null=True)
    objects = FeaturedMessageManager()

    def __unicode__(self):
        """Textual form of a featured message."""
        return u'{} - {}'.format(self.hook, self.message)
