import inspect
import logging
from functools import wraps

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

import zds.forum.signals as forum_signals
import zds.mp.signals as mp_signals
import zds.notification.signals as notification_signals
import zds.tutorialv2.signals as tuto_signals
import zds.utils.signals as utils_signals
from zds.forum.models import Forum, Post, Topic
from zds.mp.models import PrivatePost, PrivateTopic
from zds.notification.models import (
    ContentReactionAnswerSubscription,
    NewPublicationSubscription,
    NewTopicSubscription,
    Notification,
    PingSubscription,
    PrivateTopicAnswerSubscription,
    Subscription,
    TopicAnswerSubscription,
)
from zds.tutorialv2.models.database import ContentReaction, PublishableContent
from zds.utils.models import Tag

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=User.groups.through)
def remove_group_subscription_on_quitting_groups(*, sender, instance, action, pk_set, **__):
    if action not in ("pre_clear", "pre_remove"):  # only on updating
        return
    if action == "pre_clear":
        remove_group_subscription_on_quitting_groups(
            sender=sender,
            instance=instance,
            action="pre_remove",
            pk_set=set(instance.groups.values_list("pk", flat=True)),
        )
        return

    all_groups_pk = instance.groups.values_list("pk", flat=True)
    removed_groups_pk = pk_set
    kept_groups_pk = set(all_groups_pk) - set(removed_groups_pk)

    for forum in Forum.objects.filter(groups__pk__in=removed_groups_pk).exclude(groups__pk__in=kept_groups_pk):
        subscriptions = []

        forum_subscription = NewTopicSubscription.objects.get_existing(instance, forum, True)
        if forum_subscription:
            subscriptions.append(forum_subscription)

        for topic in Topic.objects.filter(forum=forum):
            topic_subscription = TopicAnswerSubscription.objects.get_existing(instance, topic, True)
            if topic_subscription:
                subscriptions.append(topic_subscription)

        for subscription in subscriptions:
            subscription.is_active = False
            if subscription.last_notification:
                subscription.last_notification.is_read = True
                subscription.last_notification.save()
            subscription.save()


def disable_for_loaddata(signal_handler):
    """
    Decorator
    Avoid the signal to be treated when sent by fixtures
    See https://code.djangoproject.com/ticket/8399#comment:7
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        for fr in inspect.stack():
            if inspect.getmodulename(fr[1]) == "loaddata":
                return
        signal_handler(*args, **kwargs)

    return wrapper


@receiver(forum_signals.post_unread, sender=Post)
def unread_topic_event(sender, *, user, post, **__):
    """
    Send a notification to the user, without sending an email.
    :param post: the post being marked as unread
    :param user: the user marking the post as unread
    """
    subscription = TopicAnswerSubscription.objects.get_existing(user, post.topic, is_active=True)
    if subscription:
        subscription.send_notification(content=post, sender=post.author, send_email=False)


@receiver(forum_signals.topic_read, sender=Topic)
@receiver(notification_signals.content_read, sender=Topic)
def mark_topic_notifications_read(sender, *, instance, user, **__):
    """
    Marks as read the notifications of the NewTopicSubscriptions and
    AnswerSubscription of the user to the topic

    :param instance: the topic marked as read
    :param user: the user reading the topic
    """
    # Subscription to the topic
    subscription = TopicAnswerSubscription.objects.get_existing(user, instance, is_active=True)
    if subscription:
        subscription.mark_notification_read()

    # Subscription to the forum
    subscription = NewTopicSubscription.objects.get_existing(user, instance.forum, is_active=True)
    if subscription:
        subscription.mark_notification_read(content=instance)

    # Subscription to the tags
    for tag in instance.tags.all():
        subscription = NewTopicSubscription.objects.get_existing(user, tag, is_active=True)
        if subscription:
            subscription.mark_notification_read(content=instance)

    content_type = ContentType.objects.get_for_model(instance)
    notifications = list(
        Notification.objects.filter(
            subscription__user=user, object_id=instance.pk, content_type__pk=content_type.pk, is_read=False
        )
    )

    for notification in notifications:
        notification.is_read = True
        notification.save(update_fields=["is_read"])


@receiver(tuto_signals.content_read, sender=PublishableContent)
@receiver(tuto_signals.content_unpublished)
def mark_content_reactions_read(sender, *, instance, user=None, target, **__):
    """
    Marks as read the notifications of the AnswerSubscription of the user to the publishable content.

    :param instance: the content marked as read
    :param user: the user reading the content
    :param target: the published content or the content reaction.

    """

    if target == ContentReaction:
        # if we marked a "user" it means we want to remove a peculiar subscription,
        # if not, all subscription related to instance are marked as read.
        if not user:
            for subscription in ContentReactionAnswerSubscription.objects.get_subscriptions(instance, True):
                subscription.mark_notification_read()
        else:
            subscription = ContentReactionAnswerSubscription.objects.get_existing(user, instance, is_active=True)
            if subscription:
                subscription.mark_notification_read()
    elif target == PublishableContent and user is not None:
        # We cannot use the list of authors of the content, because the user we
        # are subscribed to may have left the authorship of the content (see issue #5544).
        followed_users = list(NewPublicationSubscription.objects.get_objects_followed_by(user))
        if user not in followed_users:
            # When a content is published, their authors are subscribed for
            # notifications of their own publications, but these subscriptions
            # are not activated (see receiver for signal content_published).
            # Since followed_users contains only active subscriptions, current
            # user should not be in it, so we add it manually:
            followed_users.append(user)
        for followed_user in followed_users:
            subscription = NewPublicationSubscription.objects.get_existing(user, followed_user)
            if subscription:
                subscription.mark_notification_read(content=instance)


@receiver(mp_signals.topic_read, sender=PrivateTopic)
def mark_pm_reactions_read(sender, *, user, instance, **__):
    """
    Marks as read the notifications of the AnswerSubscription of the user to the private message

    :param  instance: the pm marked as read
    :param user: the user reading the pm
    """
    private_topic = instance

    subscription = PrivateTopicAnswerSubscription.objects.get_existing(user, private_topic, is_active=True)
    if subscription:
        subscription.mark_notification_read()


@receiver(mp_signals.message_unread, sender=PrivateTopic)
def unread_private_topic_event(sender, *, user, instance, **__):
    """
    Send a notification to the user, without sending an email, when a private post is marked as unread.

    :param instance: the private post being marked as unread
    :param user: the user marking the answer as unread

    """
    private_post = instance

    subscription = PrivateTopicAnswerSubscription.objects.get_existing(user, private_post.privatetopic, is_active=True)
    if subscription:
        subscription.send_notification(content=private_post, sender=private_post.author, send_email=False)


@receiver(mp_signals.participant_added, sender=PrivateTopic)
def notify_participants(sender, *, topic, silent, **__):
    """
    Subscribe participants to the private topic if not already subscribed.
    If not silent, send a notification to all participants except the author.
    The notification uses the last message of the private topic and respects email preferences.
    """
    for participant in topic.participants.all():
        subscription = PrivateTopicAnswerSubscription.objects.get_or_create_active(participant, topic)
        subscription.activate_email()
        if not silent:
            subscription.send_notification(
                content=topic.last_message,
                sender=topic.last_message.author,
                send_email=participant.profile.email_for_answer,
            )


@receiver(mp_signals.participant_removed, sender=PrivateTopic)
def clean_subscriptions(sender, *, topic, **__):
    """
    Delete all subscriptions from users not participating in the private topic.
    """
    subscriptions = PrivateTopicAnswerSubscription.objects.get_subscriptions(content_object=topic, is_active=True)
    for subscription in subscriptions:
        if not topic.is_participant(subscription.user):
            subscription.mark_notification_read()
            subscription.deactivate()


@receiver(tuto_signals.content_read, sender=ContentReaction)
@receiver(forum_signals.post_read, sender=Post)
def mark_comments_read(sender, *, instances, user, **__):
    comments = {}
    for comment in instances:
        comments[comment.pk] = comment

    subscriptions = PingSubscription.objects.filter(user=user, is_active=True, object_id__in=comments.keys())
    for subscription in subscriptions:
        subscription.mark_notification_read(comments[subscription.object_id])


@receiver(forum_signals.topic_moved, sender=Topic)
def moved_topic_event(sender, *, topic, **kwargs):
    topic_content_type = ContentType.objects.get_for_model(topic)
    _handle_private_forum_moving(topic, topic_content_type, ContentType.objects.get_for_model(topic.last_message))


@receiver(forum_signals.topic_edited, sender=Topic)
def edit_topic_event(sender, *, topic, **kwargs):
    topic_content_type = ContentType.objects.get_for_model(topic)

    # Update notification as dead if it was triggered by a deleted tag
    tag_content_type = _handle_deleted_tags(topic, topic_content_type)

    # Add notification of new topic for the subscription on the new tags
    _handle_added_tags(tag_content_type, topic)


def _handle_added_tags(tag_content_type, topic):
    for tag in topic.tags.all():
        subscriptions = NewTopicSubscription.objects.filter(
            object_id=tag.id, content_type__pk=tag_content_type.pk, is_active=True
        )
        for subscription in subscriptions:
            notification = Notification.objects.filter(object_id=topic.id, subscription=subscription)
            if not notification:
                if subscription.user != topic.author and topic.forum.can_read(subscription.user):
                    subscription.send_notification(content=topic, sender=topic.author)


def _handle_deleted_tags(topic, topic_content_type):
    tag_content_type = ContentType.objects.get_for_model(Tag)
    notifications = Notification.objects.filter(
        object_id=topic.pk, content_type__pk=topic_content_type.pk, is_read=False
    ).all()
    for notification in notifications:
        is_still_valid = notification.subscription.content_type != tag_content_type
        if not is_still_valid:
            for tag in topic.tags.all():
                if tag.id == notification.subscription.object_id:
                    is_still_valid = True
                    break
        if not is_still_valid:
            subscription = NewTopicSubscription.objects.get_existing(
                notification.subscription.user, topic.forum, is_active=True
            )
            if subscription:
                notification.subscription = subscription
            else:
                notification.is_dead = True
            notification.save()
    return tag_content_type


def _handle_private_forum_moving(topic, topic_content_type, post_content_type):
    # If the topic is moved to a restricted forum, users who cannot read this topic any more unfollow it.
    # This avoids unreachable notifications.
    TopicAnswerSubscription.objects.unfollow_and_mark_read_everybody_at(topic)
    NewTopicSubscription.objects.mark_read_everybody_at(topic)
    PingSubscription.mark_inaccessible_ping_as_read_for_topic(topic)
    # If the topic is moved to a forum followed by the user, we update the subscription of the notification.
    # Otherwise, we update the notification as dead.
    notifications = list(
        Notification.objects.filter(object_id=topic.pk, content_type__pk=topic_content_type.pk, is_read=False).all()
    )
    for notification in notifications:
        subscription = notification.subscription
        if subscription.is_active:
            notification.subscription = subscription
            notification.save()
        elif notification.subscription.content_object != notification.content_object.forum:
            notification.is_dead = True
            notification.save(update_fields=["is_dead", "is_read"])


@receiver(post_save, sender=Topic)
@disable_for_loaddata
def new_topic_event(sender, *, instance, created=True, **__):
    """
    Sends a notification to the subscribers of the forum.

    :param instance: the new topic.
    :param created: a flag set by the event to ensure the save was effective
    """
    if created:
        topic = instance

        subscriptions = NewTopicSubscription.objects.get_subscriptions(topic.forum)
        for subscription in subscriptions:
            if subscription.user != topic.author and topic.forum.can_read(subscription.user):
                subscription.send_notification(content=topic, sender=topic.author)


@receiver(post_save, sender=Post)
@disable_for_loaddata
def answer_topic_event(sender, *, instance, created=True, **__):
    """
    Sends TopicAnswerSubscription to the subscribers to the topic and subscribe
    the author to the following answers to the topic.

    :param instance: the new post.
    :param created: a flag set by the event to ensure the save was effective
    """
    if created:
        post = instance

        subscription_list = TopicAnswerSubscription.objects.get_subscriptions(post.topic)
        for subscription in subscription_list:
            if subscription.user != post.author:
                subscription.send_notification(content=post, sender=post.author)

        # Follow topic on answering
        TopicAnswerSubscription.objects.get_or_create_active(post.author, post.topic)


@receiver(post_save, sender=ContentReaction)
@disable_for_loaddata
def answer_content_reaction_event(sender, *, instance, created=True, **__):
    """
    Sends ContentReactionAnswerSubscription to the subscribers to the content reaction and
    subscribe the author to the following answers to the publishable content.

    :param instance: the new content reation.
    :param created: a flag set by the event to ensure the save was effective

    """
    if created:
        content_reaction = instance
        publishable_content = content_reaction.related_content
        author = content_reaction.author

        subscription_list = ContentReactionAnswerSubscription.objects.get_subscriptions(publishable_content)
        for subscription in subscription_list:
            if subscription.user != author:
                subscription.send_notification(content=content_reaction, sender=author)

        # Follow publishable content on answering
        ContentReactionAnswerSubscription.objects.get_or_create_active(author, publishable_content)


@receiver(tuto_signals.content_published, sender=PublishableContent)
@disable_for_loaddata
def content_published_event(*__, instance, by_email, **___):
    """
    All authors of the content follow their newly published content.

    :param instance: the new content.
    :param by_mail: Send or not an email.
    """
    content = instance
    authors = list(content.authors.all())
    for user in authors:
        if not ContentReactionAnswerSubscription.objects.get_existing(user, content):
            ContentReactionAnswerSubscription.objects.toggle_follow(content, user, by_email=by_email)
        # no need for condition here, get_or_create_active has its own
        subscription = NewPublicationSubscription.objects.get_or_create_active(user, user)
        subscription.send_notification(content=content, sender=user, send_email=by_email)
        # this allows to fix the "auto subscribe issue" but can deactivate a manually triggered subscription
        subscription.deactivate()

        for subscription in NewPublicationSubscription.objects.get_subscriptions(user).exclude(user__in=authors):
            # this condition is here to avoid exponential notifications when a user already follows one of the authors
            # while they are also among the authors.
            by_email = subscription.by_email and subscription.user.profile.email_for_answer
            subscription.send_notification(content=content, sender=user, send_email=by_email)


@receiver(mp_signals.topic_created, sender=PrivateTopic)
@disable_for_loaddata
def create_private_topic_event(sender, *, topic, by_email, **__):
    """
    Subscribe the author to the answers to the topic.

    :param topic: the new post.
    :param by_email: Send or not an email for this subscription.
    """
    subscription = PrivateTopicAnswerSubscription.objects.get_or_create_active(topic.author, topic)
    if by_email:
        subscription.activate_email()
    else:
        subscription.deactivate_email()


@receiver(mp_signals.message_added, sender=PrivatePost)
@disable_for_loaddata
def answer_private_topic_event(sender, *, post, by_email, force_email, no_notification_for=None, **__):
    """
    Sends PrivateTopicAnswerSubscription to the subscribers to the topic and subscribe
    the author to the following answers to the topic.

    :param post: the new post.
    :param by_email: Send or not an email.
    :param force_email: Send email even if the user has not enabled email notifications
    :param no_notification_for: user or group of user to ignore, really usefull when dealing with moderation message.
    """

    subscription_list = PrivateTopicAnswerSubscription.objects.get_subscriptions(post.privatetopic)
    for subscription in subscription_list:
        if subscription.user != post.author:
            is_new_mp = post.position_in_topic == 1
            send_email = force_email or (
                by_email
                and (
                    subscription.user.profile.email_for_answer
                    or (is_new_mp and subscription.user.profile.email_for_new_mp)
                )
            )
            subscription.send_notification(content=post, sender=post.author, send_email=send_email)


@receiver(pre_delete, sender=PrivateTopic)
def delete_private_topic_event(sender, instance, **__):
    """
    A private topic is deleted when there is nobody in this private topic.
    """
    subscriptions = PrivateTopicAnswerSubscription.objects.get_subscriptions(content_object=instance, is_active=True)
    for subscription in subscriptions:
        subscription.mark_notification_read()
        subscription.deactivate()


@receiver(pre_delete, sender=User)
def delete_notifications(sender, instance, **__):
    """
    Before suppression of a user, Django calls this receiver to
    delete all subscriptions and notifications linked at this member.
    """
    Subscription.objects.filter(user=instance).delete()
    Notification.objects.filter(sender=instance).delete()


@receiver(tuto_signals.content_unpublished, sender=PublishableContent)
@receiver(tuto_signals.content_unpublished, sender=ContentReaction)
def cleanup_notification_for_unpublished_content(sender, instance, **__):
    """
    Avoid persistant notification if a content is unpublished. A real talk has to be lead to avoid such cross module \
    dependency.

    :param sender: always PublishableContent
    :param instance: the unpublished content
    """
    logger.debug("deal with %s(%s) notifications.", sender, instance)
    try:
        notifications = Notification.objects.filter(
            content_type=ContentType.objects.get_for_model(instance, True), object_id=instance.pk
        )
        for notification in notifications:
            subscription = notification.subscription
            if subscription.last_notification and subscription.last_notification.pk == notification.pk:
                notification.subscription.last_notification = None
                notification.subscription.save()
            notification.delete()
        Subscription.objects.filter(
            content_type=ContentType.objects.get_for_model(instance, True), object_id=instance.pk
        ).update(is_active=False)
        logger.debug("Nothing went wrong.")
    except DatabaseError as e:
        logger.exception("Error while saving %s, %s", instance, e)


@receiver(utils_signals.ping, sender=ContentReaction)
@receiver(utils_signals.ping, sender=Post)
@disable_for_loaddata
def ping_event(sender, *, instance, user, **__):
    comment = instance
    user = user

    assert comment is not None
    assert user is not None
    if sender == Post and not instance.topic.forum.can_read(user):
        return
    subscription = PingSubscription.objects.get_or_create_active(user, comment)
    subscription.send_notification(content=comment, sender=comment.author, send_email=False)


@receiver(utils_signals.unping)
def unping_event(sender, instance, user, **_):
    if user:
        PingSubscription.objects.deactivate_subscriptions(user, instance)
