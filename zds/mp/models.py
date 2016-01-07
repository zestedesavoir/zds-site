# coding: utf-8

from math import ceil

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from zds.mp.managers import PrivateTopicManager, PrivatePostManager

from zds.utils import get_current_user, slugify


class PrivateTopic(models.Model):

    """
    Topic private, containing private posts.
    """

    class Meta:
        verbose_name = u'Message privé'
        verbose_name_plural = u'Messages privés'

    title = models.CharField(u'Titre', max_length=130)
    subtitle = models.CharField(u'Sous-titre', max_length=200, blank=True)
    author = models.ForeignKey(User, verbose_name=u'Auteur', related_name='author', db_index=True)
    participants = models.ManyToManyField(User, verbose_name=u'Participants', related_name='participants',
                                          db_index=True)
    last_message = models.ForeignKey('PrivatePost', null=True, related_name='last_message',
                                     verbose_name=u'Dernier message')
    pubdate = models.DateTimeField(u'Date de création', auto_now_add=True, db_index=True)
    objects = PrivateTopicManager()

    def __unicode__(self):
        """
        Human-readable representation of the PrivateTopic model.

        :return: PrivateTopic title
        :rtype: unicode
        """
        return self.title

    def get_absolute_url(self):
        """
        URL of a single PrivateTopic object.

        :return: PrivateTopic object URL
        :rtype: str
        """
        return reverse('private-posts-list', args=[self.pk, self.slug()])

    def slug(self):
        """
        PrivateTopic doesn't have a slug attribute of a private topic. To be compatible
        with older private topic, the slug is always re-calculate when we need one.
        :return: title slugify.
        """
        return slugify(self.title)

    def get_post_count(self):
        """
        Get the number of private posts in a single PrivateTopic object.

        :return: number of post in PrivateTopic object
        :rtype: int
        """
        return PrivatePost.objects.filter(privatetopic__pk=self.pk).count()

    def get_last_answer(self):
        """
        Get the last answer in the PrivateTopic written by topic's author, if exists.

        :return: PrivateTopic object last answer (PrivatePost)
        :rtype: PrivatePost object or None
        """
        last_post = PrivatePost.objects\
            .filter(privatetopic__pk=self.pk)\
            .order_by('-position_in_topic')\
            .first()

        # If the last post is the first post, there is no answer in the topic (only initial post)
        if last_post == self.first_post():
            return None

        return last_post

    def first_post(self):
        """
        Get the first answer in the PrivateTopic written by topic's author, if exists.

        :return: PrivateTopic object first answer (PrivatePost)
        :rtype: PrivatePost object or None
        """
        return PrivatePost.objects\
            .filter(privatetopic=self)\
            .order_by('position_in_topic')\
            .first()

    def last_read_post(self, user=None):
        """
        Get the last PrivatePost the user has read.

        :param user: The user is reading the PrivateTopic. If None, the current user is used.
        :type user: User object
        :return: last PrivatePost read
        :rtype: PrivatePost object or None
        """
        # If user param is not defined, we get the current user
        if user is None:
            user = get_current_user()

        try:
            post = PrivateTopicRead.objects\
                .select_related()\
                .filter(privatetopic=self, user=user)
            if len(post) == 0:
                return self.first_post()
            return post.latest('privatepost__position_in_topic').privatepost

        except (PrivatePost.DoesNotExist, TypeError):
            return self.first_post()

    def first_unread_post(self, user=None):
        """
        Get the first PrivatePost the user has unread.

        :param user: The user is reading the PrivateTopic. If None, the current user is used.
        :type user: User object
        :return: first PrivatePost unread
        :rtype: PrivatePost object or None
        """
        # If user param is not defined, we get the current user
        if user is None:
            user = get_current_user()

        try:
            last_post = PrivateTopicRead.objects\
                .select_related()\
                .filter(privatetopic=self, user=user)\
                .latest('privatepost__position_in_topic').privatepost

            next_post = PrivatePost.objects.filter(
                privatetopic__pk=self.pk,
                position_in_topic__gt=last_post.position_in_topic).first()

            return next_post
        except (PrivatePost.DoesNotExist, PrivateTopicRead.DoesNotExist):
            return self.first_post()

    def alone(self):
        """
        Check if there just one participant in the conversation (PrivateTopic).

        :return: True if there just one participant in PrivateTopic
        :rtype: bool
        """
        return self.participants.count() == 0

    def never_read(self, user=None):
        """
        Check if an user has never read the current PrivateTopic.

        :param user: an user as Django User object. If None, the current user is used.
        :type user: User object
        :return: True if the PrivateTopic was never read
        :rtype: bool
        """
        # If user param is not defined, we get the current user
        if user is None:
            user = get_current_user()

        return never_privateread(self, user)


class PrivatePost(models.Model):

    """A private post written by an user."""

    class Meta:
        verbose_name = u'Réponse à un message privé'
        verbose_name_plural = u'Réponses à un message privé'

    privatetopic = models.ForeignKey(PrivateTopic, verbose_name=u'Message privé', db_index=True)
    author = models.ForeignKey(User, verbose_name='Auteur', related_name='privateposts', db_index=True)
    text = models.TextField(u'Texte')
    text_html = models.TextField(u'Texte en HTML')
    pubdate = models.DateTimeField(u'Date de publication', auto_now_add=True, db_index=True)
    update = models.DateTimeField(u'Date d\'édition', null=True, blank=True)
    position_in_topic = models.IntegerField(u'Position dans le sujet', db_index=True)
    objects = PrivatePostManager()

    def __unicode__(self):
        """
        Human-readable representation of the PrivatePost model.

        :return: PrivatePost description
        :rtype: unicode
        """
        return u'<Post pour « {0} », #{1}>'.format(self.privatetopic, self.pk)

    def get_absolute_url(self):
        """
        URL of a single PrivatePost object.

        :return: PrivatePost object URL
        :rtype: str
        """
        page = int(ceil(float(self.position_in_topic) / settings.ZDS_APP['forum']['posts_per_page']))

        return '{0}?page={1}#p{2}'.format(self.privatetopic.get_absolute_url(), page, self.pk)


class PrivateTopicRead(models.Model):

    """
    Small model which keeps track of the user viewing private topics.

    It remembers the topic he looked and what was the last private Post at this time.
    """

    class Meta:
        verbose_name = u'Message privé lu'
        verbose_name_plural = u'Messages privés lus'

    privatetopic = models.ForeignKey(PrivateTopic, db_index=True)
    privatepost = models.ForeignKey(PrivatePost, db_index=True)
    user = models.ForeignKey(User, related_name='privatetopics_read', db_index=True)

    def __unicode__(self):
        """
        Human-readable representation of the PrivateTopicRead model.

        :return: PrivateTopicRead description
        :rtype: unicode
        """
        return u'<Sujet « {0} » lu par {1}, #{2}>'.format(self.privatetopic, self.user, self.privatepost.pk)


def never_privateread(privatetopic, user=None):
    """
    Check if a private topic has been read by an user since it last post was added.

    :param privatetopic: a PrivateTopic to check
    :type privatetopic: PrivateTopic object
    :param user: an user as Django User object. If None, the current user is used
    :type user: User object
    :return: True if the PrivateTopic was never read
    :rtype: bool
    """
    # If user param is not defined, we get the current user
    if user is None:
        user = get_current_user()

    return PrivateTopicRead.objects\
        .filter(privatepost=privatetopic.last_message, privatetopic=privatetopic, user=user)\
        .count() == 0


def mark_read(privatetopic, user=None):
    """
    Mark a private topic as read for the user.

    :param privatetopic: a PrivateTopic to check
    :type privatetopic: PrivateTopic object
    :param user: an user as Django User object. If None, the current user is used
    :type user: User object
    :return: nothing is returned
    :rtype: None
    """
    # If user param is not defined, we get the current user
    if user is None:
        user = get_current_user()

    # Delete the old PrivateTopic and add the new as the last read
    PrivateTopicRead.objects.filter(privatetopic=privatetopic, user=user).delete()
    topic = PrivateTopicRead(privatepost=privatetopic.last_message, privatetopic=privatetopic, user=user)
    topic.save()
