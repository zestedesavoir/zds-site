# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from zds import settings


class FeaturedResourceManager(models.Manager):
    """
    Custom featured resource manager.
    """

    def get_last_news(self):
        queryset = super(FeaturedResourceManager, self).get_queryset()
        return queryset.order_by('-pubdate')[:settings.ZDS_APP['featured_resource']['home_number']]


class FeaturedMessageManager(models.Manager):
    """
    Custom featured message manager.
    """

    def get_last_message(self):
        try:
            return super(FeaturedMessageManager, self).get_queryset().all()[:1].get()
        except ObjectDoesNotExist:
            return None
