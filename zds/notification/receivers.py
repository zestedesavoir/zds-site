# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

import inspect
from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from zds.forum.models import Topic, Post
from zds.mp.models import PrivateTopic, PrivatePost
from zds.notification.models import TopicAnswerSubscription, ContentReactionAnswerSubscription, \
    PrivateTopicAnswerSubscription, Subscription, Notification, NewTopicSubscription, NewPublicationSubscription
from zds.notification.signals import answer_unread, content_read, new_content, edit_content
from zds.tutorialv2.models.models_database import PublishableContent, ContentReaction


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
def unread_topic_event(sender, **kwargs):
    """
    :param kwargs: contains
        - instance : the answer being marked as unread
        - user : user marking the answer as unread
    Sends a notification to the user, without sending an email
    """
    answer = kwargs.get('instance')
    user = kwargs.get('user')

    subscription = TopicAnswerSubscription.objects.get_existing(user, answer.topic, is_active=True)
    if subscription:
        subscription.send_notification(content=answer, sender=answer.author, send_email=False)


@receiver(content_read, sender=Topic)
def mark_topic_notifications_read(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance : the topic marked as read
        - user : the user reading the topic
    Marks as read the notifications of the NewTopicSubscriptions and
    AnswerSubscription of the user to the topic/
    (This documentation will be okay with the v2 of ZEP-24)
    """
    topic = kwargs.get('instance')
    user = kwargs.get('user')

    # Subscription to the topic
    subscription = TopicAnswerSubscription.objects.get_existing(user, topic, is_active=True)
    if subscription:
        subscription.mark_notification_read()

    # Subscription to the forum
    subscription = NewTopicSubscription.objects.get_existing(user, topic.forum, is_active=True)
    if subscription:
        subscription.mark_notification_read(content=topic)

    content_type = ContentType.objects.get_for_model(topic)
    notifications = Notification.objects.filter(subscription__user=user, object_id=topic.pk,
                                                content_type__pk=content_type.pk, is_read=False,
                                                is_dead=True)
    for notification in notifications:
        notification.is_read = True
        notification.save()


@receiver(content_read, sender=PublishableContent)
def mark_content_reactions_read(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance: the content marked as read
        - user: the user reading the content
        - target: the published content or the content reaction.
    Marks as read the notifications of the AnswerSubscription of the user to the publishable content.
    """
    content = kwargs.get('instance')
    user = kwargs.get('user')
    target = kwargs.get('target')

    if target == ContentReaction:
        subscription = ContentReactionAnswerSubscription.objects.get_existing(user, content, is_active=True)
        if subscription:
            subscription.mark_notification_read()
    elif target == PublishableContent:
        for author in content.authors.all():
            subscription = NewPublicationSubscription.objects.get_existing(user, author, is_active=True)
            if subscription:
                subscription.mark_notification_read(content=content)


@receiver(content_read, sender=PrivateTopic)
def mark_pm_reactions_read(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance : the pm marked as read
        - user : the user reading the pm
    Marks as read the notifications of the AnswerSubscription of the user to the private message/
    (This documentation will be okay with the v2 of ZEP-24)
    """
    private_topic = kwargs.get('instance')
    user = kwargs.get('user')

    subscription = PrivateTopicAnswerSubscription.objects.get_existing(user, private_topic, is_active=True)
    if subscription:
        subscription.mark_notification_read()


@receiver(edit_content, sender=Topic)
def edit_topic_event(_, **kwargs):
    """
    :param kwargs: contains
        - instance: the topic edited.
        - action: action of the edit.
    """
    if kwargs.get('action') == 'move':
        topic = kwargs.get('instance')

        # If the topic is moved to a restricted forum, users who cannot read this topic any more unfollow it.
        # This avoids unreachable notifications.
        TopicAnswerSubscription.objects.unfollow_and_mark_read_everybody_at(topic)

        # If the topic is moved to a forum followed by the user, we update the subscription of the notification.
        # Otherwise, we update the notification as dead.
        content_type = ContentType.objects.get_for_model(topic)
        notifications = Notification.objects \
            .filter(object_id=topic.pk, content_type__pk=content_type.pk, is_read=False).all()
        for notification in notifications:
            subscription = NewTopicSubscription.objects \
                .get_existing(notification.subscription.user, topic.forum, is_active=True)
            if subscription:
                notification.subscription = subscription
                notification.save()
            elif notification.subscription.content_object != notification.content_object.forum:
                notification.is_dead = True
                notification.save()


@receiver(post_save, sender=Topic)
@disable_for_loaddata
def new_topic_event(sender, **kwargs):
    """
    :param kwargs: contains instance: the new topic.
    Sends a notification to the subscribers of the forum.
    """
    if kwargs.get('created', True):
        topic = kwargs.get('instance')

        subscriptions = NewTopicSubscription.objects.get_subscriptions(topic.forum)
        for subscription in subscriptions:
            if subscription.user != topic.author:
                subscription.send_notification(content=topic, sender=topic.author)


@receiver(post_save, sender=Post)
@disable_for_loaddata
def answer_topic_event(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance: the new post.
        - by_mail: Send or not an email.
    Sends TopicAnswerSubscription to the subscribers to the topic and subscribe
    the author to the following answers to the topic.
    """
    if kwargs.get('created', True):
        post = kwargs.get('instance')

        subscription_list = TopicAnswerSubscription.objects.get_subscriptions(post.topic)
        for subscription in subscription_list:
            if subscription.user != post.author:
                subscription.send_notification(content=post, sender=post.author)

        # Follow topic on answering
        TopicAnswerSubscription.objects.get_or_create_active(post.author, post.topic)


@receiver(post_save, sender=ContentReaction)
@disable_for_loaddata
def answer_content_reaction_event(sender, **kwargs):
    """
    :param kwargs: contains
        - instance: the new content reaction.
    Sends ContentReactionAnswerSubscription to the subscribers to the content reaction and
    subscribe the author to the following answers to the publishable content.
    """
    if kwargs.get('created', True):
        content_reaction = kwargs.get('instance')
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
def content_published_event(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance: the new content.
        - by_mail: Send or not an email.
    All authors of the content follow their new content published.
    """
    content = kwargs.get('instance')
    by_email = kwargs.get('by_email')

    for user in content.authors.all():
        ContentReactionAnswerSubscription.objects.toggle_follow(content, user, by_email=by_email)
        if not NewPublicationSubscription.objects.does_exist(user, user, is_active=True):
            NewPublicationSubscription.objects.toggle_follow(user, user, by_email=False)

        for subscription in NewPublicationSubscription.objects.get_subscriptions(user):
            by_email = subscription.by_email and subscription.user.profile.email_for_answer
            subscription.send_notification(content=content, sender=user, send_email=by_email)


@receiver(new_content, sender=PrivatePost)
@disable_for_loaddata
def answer_private_topic_event(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance: the new post.
        - by_mail: Send or not an email.
    Sends PrivateTopicAnswerSubscription to the subscribers to the topic and subscribe
    the author to the following answers to the topic.
    """
    post = kwargs.get('instance')
    by_email = kwargs.get('by_email')

    if post.position_in_topic == 1:
        # Subscribe at the new private topic all participants.
        for participant in post.privatetopic.participants.all():
            if by_email:
                PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, participant, by_email=by_email)
            else:
                PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, participant)

    subscription_list = PrivateTopicAnswerSubscription.objects.get_subscriptions(post.privatetopic)
    for subscription in subscription_list:
        if subscription.user != post.author:
            send_email = by_email and (subscription.user.profile.email_for_answer or post.position_in_topic == 1)
            subscription.send_notification(content=post, sender=post.author, send_email=send_email)

    # Follow private topic on answering
    if by_email:
        PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, post.author, by_email=by_email)
    else:
        PrivateTopicAnswerSubscription.objects.toggle_follow(post.privatetopic, post.author)


@receiver(m2m_changed, sender=PrivateTopic.participants.through)
@disable_for_loaddata
def add_participant_topic_event(sender, **kwargs):
    """
    :param kwargs:  contains
        - sender : the technical class representing the many2many relationship
        - instance : the technical class representing the many2many relationship
        - action : "pre_add", "post_add", ... action having sent the signal
        - reverse : indicates which side of the relation is updated
            (from what I understand, forward is from topic to tags, so when the tag side is modified,
            reverse is from tags to topics, so when the topics are modified)
    Sends PrivateTopicAnswerSubscription to the subscribers to the private topic.
    """

    private_topic = kwargs.get('instance')
    action = kwargs.get('action')
    relation_reverse = kwargs.get('reverse')

    # This condition is necessary because this receiver is called during the creation of the private topic.
    if private_topic.last_message:
        if action == 'post_add' and not relation_reverse:
            for participant in private_topic.participants.all():
                subscription = PrivateTopicAnswerSubscription.objects.get_or_create_active(participant, private_topic)
                subscription.send_notification(
                    content=private_topic.last_message,
                    sender=private_topic.last_message.author,
                    send_email=participant.profile.email_for_answer)

        elif action == 'post_remove' and not relation_reverse:
            subscriptions = PrivateTopicAnswerSubscription.objects \
                .get_subscriptions(content_object=private_topic, is_active=True)
            for subscription in subscriptions:
                if subscription.user not in private_topic.participants.all() \
                        and subscription.user != private_topic.author:
                    subscription.mark_notification_read()
                    subscription.deactivate()


@receiver(pre_delete, sender=PrivateTopic)
def delete_private_topic_event(sender, instance, **kwargs):
    """
    A private topic is deleted when there is nobody in this private topic.
    """
    subscriptions = PrivateTopicAnswerSubscription.objects.get_subscriptions(content_object=instance, is_active=True)
    for subscription in subscriptions:
        subscription.mark_notification_read()
        subscription.deactivate()


@receiver(pre_delete, sender=User)
def delete_notifications(sender, instance, **kwargs):
    """
    Before suppression of a user, Django calls this receiver to
    delete all subscriptions and notifications linked at this member.
    """
    Subscription.objects.filter(user=instance).delete()
    Notification.objects.filter(sender=instance).delete()
