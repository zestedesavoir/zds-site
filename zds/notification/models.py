# -*- coding: utf-8 -*-s
from django.contrib.auth.models import User
from django.db import models

from zds.forum.models import TopicRead, Topic
from zds.notification.managers import TopicFollowedManager
from zds.utils import get_current_user


class TopicFollowed(models.Model):
    """
    This model tracks which user follows which topic.
    It serves only to manual topic following.
    This model also indicates if the topic is followed by email.
    """

    class Meta:
        verbose_name = 'Sujet suivi'
        verbose_name_plural = 'Sujets suivis'

    topic = models.ForeignKey(Topic, db_index=True)
    user = models.ForeignKey(User, related_name='topics_followed', db_index=True)
    email = models.BooleanField('Notification par courriel', default=False, db_index=True)
    objects = TopicFollowedManager()

    def __unicode__(self):
        return u'<Sujet "{0}" suivi par {1}>'.format(self.topic.title,
                                                     self.user.username)


def follow(topic, user=None):
    """
    Toggle following of a topic for an user.
    :param topic: A topic.
    :param user: A user. If undefined, the current user is used.
    :return: `True` if the topic is now followed, `False` if is has been un-followed.
    """
    if user is None:
        user = get_current_user()
    try:
        existing = TopicFollowed.objects.get(topic=topic, user=user)
    except TopicFollowed.DoesNotExist:
        existing = None

    if not existing:
        # Make the user follow the topic
        topic_followed = TopicFollowed(topic=topic, user=user)
        topic_followed.save()
        return True

    # If user is already following the topic, we make him don't anymore
    existing.delete()
    return False


def follow_by_email(topic, user=None):
    """
    Toggle following by email of a topic for an user.
    :param topic: A topic.
    :param user: A user. If undefined, the current user is used.
    :return: `True` if the topic is now followed, `False` if is has been un-followed.
    """
    if user is None:
        user = get_current_user()
    try:
        existing = TopicFollowed.objects.get(topic=topic, user=user)
    except TopicFollowed.DoesNotExist:
        existing = None

    if not existing:
        # Make the user follow the topic
        topic_followed = TopicFollowed(topic=topic, user=user, email=True)
        topic_followed.save()
        return True

    existing.email = not existing.email
    existing.save()
    return existing.email


def never_read(topic, user=None):
    """
    Check if the user has read the **last post** of the topic.
    Note if the user has already read the topic but not the last post, it will consider it has never read the topic...
    Technically this is done by check if there is a `TopicRead` for the topic, its last post and the user.
    :param topic: A topic
    :param user: A user. If undefined, the current user is used.
    :return:
    """
    # TODO: cette méthode est très mal nommée en plus d'avoir un nom "booléen négatif" !
    if user is None:
        user = get_current_user()

    return not TopicRead.objects \
        .filter(post=topic.last_message, topic=topic, user=user).exists()


def mark_read(topic, user=None):
    """
    Mark the last message of a topic as read for the current user.
    :param topic: A topic.
    """
    if not user:
        user = get_current_user()

    if user and user.is_authenticated():
        # TODO: voilà entre autres pourquoi il devrait y avoir une contrainte unique sur (topic, user) sur TopicRead.
        current_topic_read = TopicRead.objects.filter(topic=topic, user=user).first()
        if current_topic_read is None:
            current_topic_read = TopicRead(post=topic.last_message, topic=topic, user=user)
        else:
            current_topic_read.post = topic.last_message
        current_topic_read.save()
