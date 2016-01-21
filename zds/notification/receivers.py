# -*- coding: utf-8 -*-
from django.contrib.auth.models import User

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
    PrivateTopicAnswerSubscription, Subscription, Notification
from zds.notification.signals import answer_unread, content_read, new_content
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

    subscription = TopicAnswerSubscription.objects.get_existing(user, topic, is_active=True)
    if subscription:
        subscription.mark_notification_read()


@receiver(content_read, sender=PublishableContent)
def mark_content_reactions_read(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance : the content marked as read
        - user : the user reading the content
    Marks as read the notifications of the AnswerSubscription of the user to the publishable content.
    """
    content_reaction = kwargs.get('instance')
    user = kwargs.get('user')

    subscription = ContentReactionAnswerSubscription.objects.get_existing(user, content_reaction, is_active=True)
    if subscription:
        subscription.mark_notification_read()


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


@receiver(pre_delete, sender=User)
def delete_notifications(sender, instance, **kwargs):
    """
    Before suppression of a user, Django calls this receiver to
    delete all subscriptions and notifications linked at this member.
    """
    Subscription.objects.filter(user=instance).delete()
    Notification.objects.filter(sender=instance).delete()
