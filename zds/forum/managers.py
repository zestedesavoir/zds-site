# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import Q


class TopicManager(models.Manager):
    """
    Custom topic manager.
    """

    def last_topics_of_a_member(self, author):
        return self.filter(author=author) \
                   .exclude(Q(forum__group__isnull=False) & ~Q(forum__group__in=author.groups.all())) \
                   .prefetch_related("author") \
                   .order_by("-pubdate") \
                   .all()[:settings.ZDS_APP['forum']['home_number']]
