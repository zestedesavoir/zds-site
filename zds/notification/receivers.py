# -*- coding: utf-8 -*-
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from zds import settings
from zds.forum.models import Topic, Post, TopicRead
from zds.mp.models import PrivateTopic
from zds.notification.models import TopicFollowed, follow


# is sent whenever an answer is set as unread
from zds.notification.signals import answer_unread, content_read, new_content
from zds.tutorialv2.models.models_database import PublishableContent


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

    # For now, we compute notifications each time we refresh each page due
    # to TopicFollowed (and TopicRead). In the v2 of the ZEP-24 with the
    # introduction of new models, these lines will be changed with something
    # better (like the usage of TopicAnswerSubscription).
    if TopicFollowed.objects.filter(user=user, topic=answer.topic).count() == 0:
        TopicFollowed(user=user, topic=answer.topic).save()


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

    # For now, we compute notifications each time we refresh each page due
    # to TopicFollowed (and TopicRead). In the v2 of the ZEP-24 with the
    # introduction of new models, we'll use NewTopicSubscriptions and
    # TopicAnswerSubscription to mark an existing notification as read.
    pass


@receiver(content_read, sender=PublishableContent)
def mark_content_reactions_read(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance : the content marked as read
        - user : the user reading the content
    Marks as read the notifications of the AnswerSubscription of the user to the content (tutorial or article)/
    (This documentation will be okay with the v2 of ZEP-24)
    """

    pass


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


# When we'll have new models, new_content will be post_save.
@receiver(new_content, sender=Post)
def answer_topic_event(sender, **kwargs):
    """
    :param kwargs:  contains
        - instance : the new post
    Sends TopicAnswerSubscription to the subscribers to the topic and subscribe
    the author to the following answers to the topic.
    (This documentation will be okay with the v2 of ZEP-24)
    """

    post = kwargs.get('instance')
    by_mail = kwargs.get('by_mail')
    topic = post.topic
    author = post.author

    # Send mail
    if by_mail:
        subject = u"{} - {} : {}".format(settings.ZDS_APP['site']['litteral_name'], _(u'Forum'), topic.title)
        from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                      settings.ZDS_APP['site']['email_noreply'])

        # get followers by email.
        followers = TopicFollowed.objects.get_followers_by_email(topic)
        for follower in followers:
            receiver = follower.user
            if receiver == author:
                continue
            last_read = TopicRead.objects.filter(
                topic=topic,
                post__position=post.position - 1,
                user=receiver).count()
            if last_read > 0:
                context = {
                    'username': receiver.username,
                    'title': topic.title,
                    'url': settings.ZDS_APP['site']['url'] + post.get_absolute_url(),
                    'author': author.username,
                    'site_name': settings.ZDS_APP['site']['litteral_name']
                }
                message_html = render_to_string('email/forum/new_post.html', context)
                message_txt = render_to_string('email/forum/new_post.txt', context)

                msg = EmailMultiAlternatives(subject, message_txt, from_email, [receiver.email])
                msg.attach_alternative(message_html, "text/html")
                msg.send()

    # Follow topic on answering
    if not TopicFollowed.objects.is_followed(topic, user=author):
        follow(topic)
