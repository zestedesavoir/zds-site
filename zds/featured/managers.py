# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from zds import settings


class ResourceFeaturedManager(models.Manager):
    """
    Custom featured manager.
    """

    def get_last_news(self):
        queryset = super(ResourceFeaturedManager, self).get_queryset()
        return queryset.order_by('-pubdate')[:settings.ZDS_APP['featured']['home_number']]


class MessageFeaturedManager(models.Manager):
    """
    Custom message featured manager.
    """

    def get_last_message(self):
        try:
            return super(MessageFeaturedManager, self).get_queryset().all()[:1].get()
        except ObjectDoesNotExist:
            return None
