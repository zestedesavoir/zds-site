# -*- coding: utf-8 -*-
from django.db import models

from zds.utils import get_current_user


class TopicFollowedManager(models.Manager):
    def get_followers_by_email(self, topic):
        """
        :return: the set of users that follows this topic by email.
        """
        return self.filter(topic=topic, email=True).select_related("user")

    def is_followed(self, topic, user=None):
        """
        Checks if the user follows this topic.
        :param user: An user. If undefined, the current user is used.
        :return: `True` if the user follows this topic, `False` otherwise.
        """
        if user is None:
            user = get_current_user()

        return self.filter(topic=topic, user=user).exists()
