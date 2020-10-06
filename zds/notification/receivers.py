import inspect
import logging

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError
from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver

from zds.forum.models import Topic, Post, Forum
from zds.mp.models import PrivateTopic, PrivatePost
from zds.mp.signals import participant_added, participant_removed
from zds.notification.models import TopicAnswerSubscription, ContentReactionAnswerSubscription, \
    PrivateTopicAnswerSubscription, Subscription, Notification, NewTopicSubscription, NewPublicationSubscription, \
    PingSubscription
from zds.notification.signals import answer_unread, content_read, new_content, edit_content, unsubscribe
from zds.tutorialv2.models.database import PublishableContent, ContentReaction
from zds.tutorialv2.signals import content_unpublished
from zds.utils.models import Tag

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=User.groups.through)
def remove_group_subscription_on_quitting_groups(*, sender, instance, action, pk_set, **__):
    if action not in ('pre_clear', 'pre_remove'):  # only on updating
        return
    if action == 'pre_clear':

        remove_group_subscription_on_quitting_groups(sender=sender, instance=instance, action='pre_remove',
                                                     pk_set=set(instance.groups.values_list('pk', flat=True)))
        return

    for forum in Forum.objects.filter(groups__pk__in=list(pk_set)):
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
            if inspect.getmodulename(fr[1]) == 'loaddata':
                return
        signal_handler(*args, **kwargs)
    return wrapper


@receiver(answer_unread, sender=Topic)
def unread_topic_event(sender, *, user, instance, **__):
    """
    Sends a notification to the user, without sending an email

    :param instance: the answer being marked as unread
    :param user: user marking the answer as unread

    """
    subscription = TopicAnswerSubscription.objects.get_existing(user, instance.topic, is_active=True)
    if subscription:
        subscription.send_notification(content=instance, sender=instance.author, send_email=False)


@receiver(content_read, sender=Topic)
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
    notifications = list(Notification.objects.filter(subscription__user=user, object_id=instance.pk,
                                                     content_type__pk=content_type.pk, is_read=False))

    for notification in notifications:
        notification.is_read = True
        notification.save(update_fields=['is_read'])


@receiver(content_read, sender=PublishableContent)
@receiver(content_unpublished)
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
    elif target == PublishableContent:
        authors = list(instance.authors.all())
        for author in authors:
            subscription = NewPublicationSubscription.objects.get_existing(user, author)
            # a subscription has to be handled only if it is active OR if it was triggered from the publication
            # event that creates an "autosubscribe" which is immediately deactivated.
            if subscription and (subscription.is_active or subscription.user in authors):
                subscription.mark_notification_read(content=instance)


@receiver(content_read, sender=PrivateTopic)
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


@receiver(answer_unread, sender=PrivateTopic)
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


@receiver(participant_added, sender=PrivateTopic)
def notify_participants(sender, *, topic, **__):
    """
    Show a notification to all participants of a private topic except the author.
    The notification uses the last message of the private topic and respects email preferences.
    """
    for participant in topic.participants.all():
        subscription = PrivateTopicAnswerSubscription.objects.get_or_create_active(participant, topic)
        subscription.send_notification(
            content=topic.last_message,
            sender=topic.last_message.author,
            send_email=participant.profile.email_for_answer)


@receiver(participant_removed, sender=PrivateTopic)
def clean_subscriptions(sender, *, topic, **__):
    """
    Delete all subscriptions from users not participating in the private topic.
    """
    subscriptions = PrivateTopicAnswerSubscription.objects.get_subscriptions(content_object=topic, is_active=True)
    for subscription in subscriptions:
        if not topic.is_participant(subscription.user):
            subscription.mark_notification_read()
            subscription.deactivate()


@receiver(content_read, sender=ContentReaction)
@receiver(content_read, sender=Post)
def mark_comment_read(sender, *, instance, user, **__):
    comment = instance

    subscription = PingSubscription.objects.get_existing(user, comment, is_active=True)
    if subscription:
        subscription.mark_notification_read(comment)


@receiver(edit_content, sender=Topic)
def edit_topic_event(sender, *, action, instance, **kwargs):
    """
    :param kwargs: contains
        - instance: the topic edited.
        - action: action of the edit.
    """
    topic = instance
    topic_content_type = ContentType.objects.get_for_model(topic)

    if action == 'move':

        _handle_private_forum_moving(topic, topic_content_type, ContentType.objects.get_for_model(topic.last_message))

    elif action == 'edit_tags_and_title':
        topic = instance

        # Update notification as dead if it was triggered by a deleted tag
        tag_content_type = _handle_deleted_tags(topic, topic_content_type)

        # Add notification of new topic for the subscription on the new tags
        _handle_added_tags(tag_content_type, topic)


def _handle_added_tags(tag_content_type, topic):
    for tag in topic.tags.all():
        subscriptions = NewTopicSubscription.objects.filter(
            object_id=tag.id, content_type__pk=tag_content_type.pk, is_active=True)
        for subscription in subscriptions:
            notification = Notification.objects.filter(object_id=topic.id, subscription=subscription)
            if not notification:
                if subscription.user != topic.author:
                    subscription.send_notification(content=topic, sender=topic.author)


def _handle_deleted_tags(topic, topic_content_type):
    tag_content_type = ContentType.objects.get_for_model(Tag)
    notifications = Notification.objects \
        .filter(object_id=topic.pk, content_type__pk=topic_content_type.pk, is_read=False).all()
    for notification in notifications:
        is_still_valid = notification.subscription.content_type != tag_content_type
        if not is_still_valid:
            for tag in topic.tags.all():
                if tag.id == notification.subscription.object_id:
                    is_still_valid = True
                    break
        if not is_still_valid:
            subscription = NewTopicSubscription.objects \
                .get_existing(notification.subscription.user, topic.forum, is_active=True)
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
    notifications = list(Notification.objects
                         .filter(object_id=topic.pk, content_type__pk=topic_content_type.pk, is_read=False).all())
    for notification in notifications:
        subscription = notification.subscription
        if subscription.is_active:
            notification.subscription = subscription
            notification.save()
        elif notification.subscription.content_object != notification.content_object.forum:
            notification.is_dead = True
            notification.save(update_fields=['is_dead', 'is_read'])


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
            if subscription.user != topic.author:
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


@receiver(new_content, sender=PublishableContent)
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


@receiver(new_content, sender=ContentReaction)
@receiver(new_content, sender=Post)
@disable_for_loaddata
def answer_comment_event(sender, *, instance, user, **__):
    comment = instance
    user = user

    assert comment is not None
    assert user is not None
    if sender == Post and not instance.topic.forum.can_read(user):
        return
    subscription = PingSubscription.objects.get_or_create_active(user, comment)
    subscription.send_notification(content=comment, sender=comment.author, send_email=False)


@receiver(new_content, sender=PrivatePost)
@disable_for_loaddata
def answer_private_topic_event(sender, *, instance, by_email, no_notification_for=None, **__):
    """
    Sends PrivateTopicAnswerSubscription to the subscribers to the topic and subscribe
    the author to the following answers to the topic.

    :param instance: the new post.
    :param by_email: Send or not an email.
    :param no_notification_for: user or group of user to ignore, really usefull when dealing with moderation message.
    """
    post = instance

    if post.position_in_topic == 1:
        # Subscribe the author.
        if by_email:
            PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, post.author, by_email=by_email)
        else:
            PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, post.author)
        # Subscribe at the new private topic all participants.
        for participant in post.privatetopic.participants.all():
            if no_notification_for and (participant == no_notification_for or participant in no_notification_for):
                continue
            if by_email:
                PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, participant, by_email=by_email)
            else:
                PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, participant)

    subscription_list = PrivateTopicAnswerSubscription.objects.get_subscriptions(post.privatetopic)
    for subscription in subscription_list:
        if subscription.user != post.author:
            is_new_mp = post.position_in_topic == 1
            send_email = by_email and (subscription.user.profile.email_for_answer or (is_new_mp and subscription.user
                                                                                      .profile.email_for_new_mp))
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


@receiver(content_unpublished, sender=PublishableContent)
@receiver(content_unpublished, sender=ContentReaction)
def cleanup_notification_for_unpublished_content(sender, instance, **__):
    """
    Avoid persistant notification if a content is unpublished. A real talk has to be lead to avoid such cross module \
    dependency.

    :param sender: always PublishableContent
    :param instance: the unpublished content
    """
    logger.debug('deal with %s(%s) notifications.', sender, instance)
    try:
        notifications = Notification.objects\
            .filter(content_type=ContentType.objects.get_for_model(instance, True),
                    object_id=instance.pk)
        for notification in notifications:
            subscription = notification.subscription
            if subscription.last_notification and subscription.last_notification.pk == notification.pk:
                notification.subscription.last_notification = None
                notification.subscription.save()
            notification.delete()
        Subscription.objects.filter(content_type=ContentType.objects.get_for_model(instance, True),
                                    object_id=instance.pk).update(is_active=False)
        logger.debug('Nothing went wrong.')
    except DatabaseError as e:
        logger.exception('Error while saving %s, %s', instance, e)


@receiver(unsubscribe)
def unsubscripte_unpinged_user(sender, instance, user, **_):
    if user:
        PingSubscription.objects.deactivate_subscriptions(user, instance)
