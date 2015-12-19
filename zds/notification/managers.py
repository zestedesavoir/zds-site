# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from zds.utils import get_current_user


class SubscriptionManager(models.Manager):
    """
    Custom subscription manager
    """

    def get_existing(self, profile, content_object, is_active=None):
        content_type = ContentType.objects.get_for_model(content_object)
        try:
            if is_active is None:
                existing = self.get(
                    object_id=content_object.pk,
                    content_type__pk=content_type.pk,
                    profile=profile)
            else:
                existing = self.get(
                    object_id=content_object.pk,
                    content_type__pk=content_type.pk,
                    profile=profile, is_active=is_active)
        except ObjectDoesNotExist:
            existing = None
        return existing

    def get_or_create_active(self, profile, content_object):
        content_type = ContentType.objects.get_for_model(content_object)
        try:
            subscription = self.get(
                object_id=content_object.pk,
                content_type__pk=content_type.pk,
                profile=profile)
            if not subscription.is_active:
                subscription.activate()
        except ObjectDoesNotExist:
            subscription = self.model(profile=profile, content_object=content_object)
            subscription.save()

        return subscription

    def get_subscribers(self, content_object, only_by_email=False):
        users = []

        content_type = ContentType.objects.get_for_model(content_object)
        if only_by_email:
            # if I'm only interested by the email subscription
            subscription_list = self.filter(
                object_id=content_object.pk,
                content_type__pk=content_type.pk,
                by_email=True)
        else:
            subscription_list = self.filter(
                object_id=content_object.pk,
                content_type__pk=content_type.pk)

        for subscription in subscription_list:
            users.append(subscription.profile.user)
        return users

    def get_objects_followed_by(self, profile):
        """
        :return: All objects followed by this user.
        """
        followed_objects = []
        subscription_list = self.filter(profile=self, is_active=True)\
            .order_by('last_notification__pubdate')

        for subscription in subscription_list:
            followed_objects.append(subscription.content_object)

        return followed_objects


class NotificationManager(models.Manager):
    """
    Custom notification manager.
    """

    def get_unread_notifications_of(self, profile):
        """
        Gets all notifications for a user whose profile is passed as argument.

        :param profile: user's profile object
        :type profile: zds.members.models.Profile
        :return: an iterable over notifications with user data already loaded
        :rtype: QuerySet
        """
        return self.filter(subscription__profile=profile, is_read=False) \
            .select_related("sender") \
            .select_related("sender__user")

    def filter_content_type_of(self, model):
        content_subscription_type = ContentType.objects.get_for_model(model)
        return self.filter(subscription__content_type__pk=content_subscription_type.pk)


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
