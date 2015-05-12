# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import Q


class ForumManager(models.Manager):
    """
    Custom forum manager.
    """

    def get_public_forums_of_category(self, category):
        return self.filter(category=category, group__isnull=True).select_related("category").distinct().all()

    def get_private_forums_of_category(self, category, user):
        return self.filter(category=category, group__in=user.groups.all())\
            .order_by('position_in_category')\
            .select_related("category").distinct().all()


class TopicManager(models.Manager):
    """
    Custom topic manager.
    """

    def last_topics_of_a_member(self, author, user):
        """
        Gets last topics of a member but exclude all topics not accessible
        for the request user.
        :param author: Author of topics.
        :param user: Request user.
        :return: List of topics.
        """
        return self.filter(author=author) \
                   .exclude(Q(forum__group__isnull=False) & ~Q(forum__group__in=user.groups.all())) \
                   .prefetch_related("author") \
                   .order_by("-pubdate") \
                   .all()[:settings.ZDS_APP['forum']['home_number']]

    def get_beta_topic_of(self, tutorial):
        return self.filter(key=tutorial.pk, key__isnull=False).first()

    def get_last_topics(self):
        return self.order_by('-pubdate') \
                   .all()[:settings.ZDS_APP['topic']['home_number']]


class PostManager(models.Manager):
    """
    Custom post manager.
    """

    def get_messages_of_a_topic(self, topic_pk):
        return self.filter(topic__pk=topic_pk).select_related("author__profile").order_by("position").all()
