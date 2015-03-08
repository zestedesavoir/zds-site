# coding: utf-8

from django.db import models

from zds.gallery.models import Image

from zds.member.models import Profile


class News(models.Model):
    class Meta:
        verbose_name = 'Une'
        verbose_name_plural = 'Unes'

    title = models.CharField(u'Titre', max_length=80)
    type = models.CharField(u'Type', max_length=80)
    authors = models.ManyToManyField(Profile, verbose_name='Auteurs', db_index=True)
    image = models.ForeignKey(
        Image, verbose_name='Image de la une', blank=False, null=False
    )
    avatar_url = models.CharField(
        'URL de la une', max_length=256, null=False, blank=False
    )

    def __unicode__(self):
        """Textual form of a news."""
        return self.title
