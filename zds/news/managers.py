# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist

from django.db import models
from zds import settings


class NewsManager(models.Manager):
    """
    Custom news manager.
    """

    def get_last_news(self):
        return super(NewsManager, self).get_queryset().order_by('-pubdate')[:settings.ZDS_APP['news']['home_number']]


class MessageNewsManager(models.Manager):
    """
    Custom message news manager.
    """

    def get_last_message(self):
        try:
            return super(MessageNewsManager, self).get_queryset().all()[:1].get()
        except ObjectDoesNotExist:
            return None
