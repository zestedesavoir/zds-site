# -*- coding: utf-8 -*-
from datetime import datetime

from django.db import models

from zds import settings


class FeaturedResourceManager(models.Manager):
    """
    Custom featured resource manager.
    """

    def get_last_featured(self):
        return self.order_by('-pubdate') \
            .exclude(pubdate__gt=datetime.now()) \
            .prefetch_related('authors__user')[:settings.ZDS_APP['featured_resource']['home_number']]


class FeaturedMessageManager(models.Manager):
    """
    Custom featured message manager.
    """

    def get_last_message(self):
        return self.last()
