from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from zds.forum.models import Topic
from zds.notification import signals
from zds.utils import get_current_user


class SubscriptionManager(models.Manager):
    """
    Custom subscription manager
    """

    def __create_lookup_args(self, user, content_object, is_active, by_email):
        """
        Generates QuerySet lookup parameters for use with get(), filter(), ...
        """
        content_type = ContentType.objects.get_for_model(content_object)
        lookup = dict(object_id=content_object.pk, content_type__pk=content_type.pk, user=user)
        if is_active is not None:
            lookup["is_active"] = is_active
        if by_email is not None:
            lookup["by_email"] = by_email
        return lookup

    def get_existing(self, user, content_object, is_active=None, by_email=None):
        """
        If exists, return the existing subscription for the given user and content object.

        :param user: concerned user.
        :type user: django.contrib.auth.models.User
        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :param is_active: Boolean to know if we want a subscription active or not.
        :type is_active: Boolean
        :param by_email: Boolean to know if we want a subscription for email or not.
        :type by_email: Boolean
        :return: subscription or None
        """
        lookup = self.__create_lookup_args(user, content_object, is_active, by_email)
        try:
            existing = self.get(**lookup)
        except ObjectDoesNotExist:
            existing = None
        return existing

    def does_exist(self, user, content_object, is_active=None, by_email=None):
        """
        Check if there is a subscription for the given user and content object.

        :param user: concerned user.
        :type user: django.contrib.auth.models.User
        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :param is_active: Boolean to know if we want a subscription active or not.
        :type is_active: Boolean
        :param by_email: Boolean to know if we want a subscription for email or not.
        :type by_email: Boolean
        :return: Boolean, whether this subscription exists or not
        """
        lookup = self.__create_lookup_args(user, content_object, is_active, by_email)
        return self.filter(**lookup).exists()

    def get_or_create_active(self, user, content_object):
        """
        Gets (or create if it doesn't exist) the subscription for the content object given.

        :param user: concerned user.
        :type user: django.contrib.auth.models.User
        :param content_object: Generic content concerned.
        :type content_object: instance concerned by notifications
        :return: subscription
        """
        content_type = ContentType.objects.get_for_model(content_object)
        try:
            subscription = self.get(object_id=content_object.pk, content_type__pk=content_type.pk, user=user)
            if not subscription.is_active:
                subscription.activate()
        except ObjectDoesNotExist:
            subscription = self.model(user=user, content_object=content_object)
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
        return self.filter(object_id=content_object.pk, content_type__pk=content_type.pk, is_active=is_active)

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
                object_id=content_object.pk, content_type__pk=content_type.pk, by_email=True
            )
        else:
            subscription_list = self.filter(object_id=content_object.pk, content_type__pk=content_type.pk)

        return [subscription.user for subscription in subscription_list]

    def toggle_follow(self, content_object, user=None, by_email=False):
        """
        Toggle following of a resource notifiable for a user.

        :param content_object: A resource notifiable.
        :param user: A user. If undefined, the current user is used.
        :param by_email: Get subscription by email or not.
        :return: subscription of the user for the content.
        """
        if not user:
            user = get_current_user()
        if by_email:
            existing = self.get_existing(user, content_object, is_active=True, by_email=True)
        else:
            existing = self.get_existing(user, content_object, is_active=True)
        if not existing:
            subscription = self.get_or_create_active(user, content_object)
            if by_email:
                subscription.activate_email()
            return subscription
        signals.content_read.send(
            sender=content_object.__class__, instance=content_object, user=user, target=content_object.__class__
        )
        if by_email:
            existing.deactivate_email()
        else:
            existing.deactivate()
        return existing

    def deactivate_subscriptions(self, user, _object):
        subscription = self.get_existing(user, _object)
        if subscription:
            subscription.is_active = False
            notification = subscription.last_notification
            notification.is_read = True
            notification.is_dead = True
            notification.save(update_fields=["is_read", "is_dead"])
            subscription.save(update_fields=["is_active"])


class NewPublicationSubscriptionManager(SubscriptionManager):
    def get_objects_followed_by(self, user):
        """
        Gets objects followed by the given user.

        :param user: concerned user.
        :type user: django.contrib.auth.models.User
        :return: All objects followed by given user.
        """
        user_list = self.filter(
            user=user, is_active=True, content_type=ContentType.objects.get_for_model(User)
        ).values_list("object_id", flat=True)

        return User.objects.filter(id__in=user_list)


class NewTopicSubscriptionManager(SubscriptionManager):
    def mark_read_everybody_at(self, topic):
        """
        Mark every unaccessible notifications as read.

        :param topic:
        :return:
        """
        from zds.notification.models import Notification

        notifications = Notification.objects.filter(
            content_type__pk=ContentType.objects.get_for_model(topic).pk, object_id=topic.pk
        )
        for notification in notifications:
            if not topic.forum.can_read(notification.subscription.user):
                notification.is_read = True
                notification.save()


class TopicAnswerSubscriptionManager(SubscriptionManager):
    """
    Custom topic answer subscription manager.
    """

    def get_objects_followed_by(self, user):
        """
        Gets objects followed by the given user.

        :param user: concerned user.
        :type user: django.contrib.auth.models.User
        :return: All objects followed by given user.
        """
        topic_list = self.filter(
            user=user, is_active=True, content_type=ContentType.objects.get_for_model(Topic)
        ).values_list("object_id", flat=True)

        return (
            Topic.objects.filter(id__in=topic_list)
            .select_related("solved_by", "last_message")
            .order_by("-last_message__pubdate")
        )

    def unfollow_and_mark_read_everybody_at(self, topic):
        """
        Deactivate a subscription at a topic and mark read the notification associated if exist.

        :param topic: topic concerned.
        :type topic: zds.forum.models.Topic
        """
        subscriptions = self.get_subscriptions(topic)
        for subscription in subscriptions:
            if not topic.forum.can_read(subscription.user):
                subscription.deactivate()
                subscription.mark_notification_read()


class NotificationManager(models.Manager):
    """
    Custom notification manager.
    """

    def get_notifications_of(self, user):
        """
        Gets all notifications of a user.

        :param user: user object.
        :return: a queryset of notifications.
        """
        return self.filter(subscription__user=user).select_related("sender")

    def get_unread_notifications_of(self, user):
        """
        Gets all notifications for a user whose user is passed as argument.

        :param user: user object
        :type user: django.contrib.auth.models.User
        :return: an iterable over notifications with user data already loaded
        :rtype: an iterable list of notifications
        """
        return self.filter(subscription__user=user, is_read=False).select_related("sender")

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
        Gets all users who have an notification unread on the given content object.

        :param content_object: generic content object.
        :type content_object: instance concerned by notifications
        :return: an iterable list of users.
        """
        content_type = ContentType.objects.get_for_model(content_object)
        notifications = (
            self.filter(object_id=content_object.pk, content_type__pk=content_type.pk)
            .select_related("subscription")
            .select_related("subscription__user")
        )
        return [notification.subscription.user for notification in notifications]


class TopicFollowedManager(models.Manager):
    def get_followers_by_email(self, topic):
        """
        :return: the set of users who follow this topic by email.
        """
        return self.filter(topic=topic, email=True).select_related("user")

    def is_followed(self, topic, user=None):
        """
        Checks if the user follows this topic.
        :param user: A user. If undefined, the current user is used.
        :return: `True` if the user follows this topic, `False` otherwise.
        """
        if user is None:
            user = get_current_user()

        return self.filter(topic=topic, user=user).exists()
