# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from zds.utils import get_current_user


class SubscriptionManager(models.Manager):
    """
    Custom subscription manager
    """

    def get_existing(self, profile, content_object, is_active=None, by_email=None):
        """
        If exists, return the existing subscription for the profile and content object given.

        :param profile: Profile concerned.
        :type profile: zds.members.models.Profile
        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :param is_active: Boolean to know if we want a subscription active or not.
        :type is_active: Boolean
        :param by_email: Boolean to know if we want a subscription for email or not.
        :type by_email: Boolean
        :return: subscription or None
        """
        content_type = ContentType.objects.get_for_model(content_object)
        try:
            if is_active is None and by_email is None:
                existing = self.get(
                    object_id=content_object.pk,
                    content_type__pk=content_type.pk,
                    profile=profile)
            elif is_active is not None and by_email is None:
                existing = self.get(
                    object_id=content_object.pk,
                    content_type__pk=content_type.pk,
                    profile=profile, is_active=is_active)
            elif is_active is None and by_email is not None:
                existing = self.get(
                    object_id=content_object.pk,
                    content_type__pk=content_type.pk,
                    profile=profile, by_email=by_email)
            else:
                existing = self.get(
                    object_id=content_object.pk,
                    content_type__pk=content_type.pk,
                    profile=profile, is_active=is_active,
                    by_email=by_email)
        except ObjectDoesNotExist:
            existing = None
        return existing

    def get_or_create_active(self, profile, content_object):
        """
        Gets (or create if it doesn't exist) the subscription for the content object given.

        :param profile: Profile concerned.
        :type profile: zds.members.models.Profile
        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :return: subscription
        """
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

    def get_subscriptions(self, content_object, is_active=True):
        """
        Gets subscriptions of the content object.

        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :param is_active: Boolean to know if we want a subscription active or not.
        :type is_active: Boolean
        :return: an iterable list of subscriptions
        """
        content_type = ContentType.objects.get_for_model(content_object)
        return self.filter(object_id=content_object.pk,
                           content_type__pk=content_type.pk,
                           is_active=is_active)

    def get_subscribers(self, content_object, only_by_email=False):
        """
        Gets all subscribers of a content object.

        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :param only_by_email: Boolean to know if we want a subscription for email or not.
        :type only_by_email: Boolean
        :return: users
        """
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

        return [subscription.profile.user for subscription in subscription_list]

    def get_objects_followed_by(self, profile):
        """
        Gets objects followed by the profile given.

        :param profile: Profile concerned.
        :type profile: zds.members.models.Profile
        :return: All objects followed by given user.
        """
        subscription_list = self.filter(profile=profile, is_active=True) \
            .order_by('last_notification__pubdate')

        return [subscription.content_object for subscription in subscription_list]

    def toggle_follow(self, content_object, user=None, by_email=None):
        """
        Toggle following of a resource notifiable for a user.
        :param content_object: A resource notifiable.
        :param user: A user. If undefined, the current user is used.
        :param by_email: Get subscription by email or not.
        :return: subscription of the user for the content.
        """
        if user is None:
            user = get_current_user()
        if by_email:
            existing = self.get_existing(user.profile, content_object, is_active=True, by_email=True)
        else:
            existing = self.get_existing(user.profile, content_object, is_active=True)
        if existing is None:
            subscription = self.get_or_create_active(user.profile, content_object)
            if by_email:
                subscription.activate_email()
            return subscription
        if by_email:
            existing.deactivate_email()
        else:
            existing.deactivate()
        return existing


class TopicAnswerSubscriptionManager(SubscriptionManager):
    """
    Custom topic answer subscription manager.
    """
    def unfollow_and_mark_read_everybody_at(self, topic):
        """
        Deactivate a subscription at a topic and mark read the notification associated if exist.

        :param topic: topic concerned.
        :type topic: zds.forum.models.Topic
        """
        subscriptions = self.get_subscriptions(topic)
        for subscription in subscriptions:
            if not topic.forum.can_read(subscription.profile.user):
                subscription.deactivate()
                subscription.mark_notification_read()


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
        :rtype: an iterable list of notifications
        """
        return self.filter(subscription__profile=profile, is_read=False) \
            .select_related("sender") \
            .select_related("sender__user")

    def filter_content_type_of(self, model):
        """
        Applies a filter on the content_type.

        :param model: Model concerned for the ContentType
        :type model: Model concerned by notifications
        :return: an iterable list of notifications
        """
        content_subscription_type = ContentType.objects.get_for_model(model)
        return self.filter(subscription__content_type__pk=content_subscription_type.pk)

    def get_users_for_unread_notification_on(self, content_object):
        """
        Gets all users which have an notification unread on the given content object.

        :param content_object: generic content object.
        :type content_object: instance concerned by notifications
        :return: an iterable list of users.
        """
        content_type = ContentType.objects.get_for_model(content_object)
        notifications = self.filter(object_id=content_object.pk, content_type__pk=content_type.pk) \
            .select_related("subscription") \
            .select_related("subscription__profile") \
            .select_related("subscription__profile__user")
        return [notification.subscription.profile.user for notification in notifications]


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
