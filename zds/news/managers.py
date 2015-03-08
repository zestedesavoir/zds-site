# -*- coding: utf-8 -*-

from django.db import models
from zds import settings


class NewsManager(models.Manager):
    """
    Custom profile manager.
    """

    def get_last_news(self):
        return super(NewsManager, self).get_queryset().order_by('-pubdate')[:settings.ZDS_APP['news']['home_number']]
