# coding: utf-8

from django.db import models

from zds.member.models import Profile


class News(models.Model):
    class Meta:
        verbose_name = u'Une'
        verbose_name_plural = u'Unes'

    title = models.CharField(u'Titre', max_length=80)
    type = models.CharField(u'Type', max_length=80)
    authors = models.ManyToManyField(Profile, verbose_name=u'Auteurs', db_index=True)
    image_url = models.CharField(
        u'URL de la une', max_length=128, null=False, blank=False
    )
    url = models.CharField(
        u'URL de la une', max_length=128, null=False, blank=False
    )

    def __unicode__(self):
        """Textual form of a news."""
        return self.title
