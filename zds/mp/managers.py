from django.db import models
from django.db.models import Q


class PrivateTopicManager(models.Manager):
    """
    Custom private topic manager.
    """

    def get_private_topics_of_user(self, user_id):
        return (
            super()
            .get_queryset()
            .filter(Q(participants__in=[user_id]) | Q(author=user_id))
            .select_related("author__profile")
            .prefetch_related("participants")
            .distinct()
            .order_by("-last_message__pubdate")
            .all()
        )

    def get_private_topics_selected(self, user_id, pks):
        return super().get_queryset().filter(pk__in=pks).filter(Q(participants__in=[user_id]) | Q(author=user_id))


class PrivatePostManager(models.Manager):
    def get_message_of_a_private_topic(self, private_topic_id):
        return (
            super()
            .get_queryset()
            .select_related("hat")
            .filter(privatetopic__pk=private_topic_id)
            .order_by("position_in_topic")
            .all()
        )
