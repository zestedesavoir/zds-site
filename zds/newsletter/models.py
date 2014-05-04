# coding: utf-8

from django.db import models


class Newsletter(models.Model):

    """Newsletter list."""
    class Meta:
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletter'

    email = models.CharField('email', max_length=80)
    ip = models.CharField('ip_adress', max_length=20)

    def __unicode__(self):
        """Textual Newsletter."""
        return self.email
