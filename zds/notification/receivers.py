# -*- coding: utf-8 -*-
from django.contrib.auth.models import User

from functools import wraps

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from zds.forum.models import Topic, Post
from zds.mp.models import PrivateTopic
from zds.notification.models import TopicAnswerSubscription, ContentReactionAnswerSubscription, \
    Subscription, Notification
from zds.notification.signals import answer_unread, content_read
from zds.tutorialv2.models.models_database import PublishableContent, ContentReaction


def disable_for_loaddata(signal_handler):
    """
    Decorator
    Avoid the signal to be treated when sent by fixtures
    """
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if "raw" in kwargs and kwargs['raw']:
            print "Skipping signal for %s %s" % (args, kwargs)
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

    subscription = TopicAnswerSubscription.objects.get_existing(user.profile, answer.topic, is_active=True)
    if subscription:
        subscription.send_notification(content=answer, sender=answer.author.profile, send_email=False)


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

    subscription = TopicAnswerSubscription.objects.get_existing(user.profile, topic, is_active=True)
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

    subscription = ContentReactionAnswerSubscription.objects\
        .get_existing(user.profile, content_reaction, is_active=True)
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

    pass


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
            if subscription.profile != post.author.profile:
                subscription.send_notification(content=post, sender=post.author.profile)

        # Follow topic on answering
        TopicAnswerSubscription.objects.get_or_create_active(post.author.profile, post.topic)


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
        author = content_reaction.author.profile

        subscription_list = ContentReactionAnswerSubscription.objects.get_subscriptions(publishable_content)
        for subscription in subscription_list:
            if subscription.profile != author:
                subscription.send_notification(content=content_reaction, sender=author)

        # Follow publishable content on answering
        ContentReactionAnswerSubscription.objects.get_or_create_active(author, publishable_content)


@receiver(pre_delete, sender=User)
def delete_notifications(sender, instance, **kwargs):
    """
    Before suppression of a user, Django calls this receiver to
    delete all subscriptions and notifications linked at this member.
    """
    Subscription.objects.filter(profile=instance.profile).delete()
    Notification.objects.filter(sender=instance.profile).delete()
