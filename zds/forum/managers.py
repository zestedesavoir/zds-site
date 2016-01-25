# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from model_utils.managers import InheritanceManager


class ForumManager(models.Manager):
    """
    Custom forum manager.
    """

    def get_public_forums_of_category(self, category, with_count=False):
        """load all public forums for a category

        :param category: the related category
        :type category: zds.forum.models.Category
        :param with_count: optional parameter: if true, will preload thread and post number for each forum inside \
        category
        :type with_count: bool
        """
        query_set = self.filter(category=category, group__isnull=True).select_related("category").distinct()
        if with_count:
            # this request count the threads in each forum
            thread_sub_query = "SELECT COUNT(*) FROM forum_topic WHERE forum_topic.forum_id=forum_forum.id"
            # this request count the posts in each forum
            post_sub_query = "SELECT COUNT(*) FROM forum_post WHERE forum_post.topic_id " \
                             "IN(SELECT id FROM forum_topic WHERE forum_topic.forum_id=forum_forum.id)"

            query_set = query_set.extra(select={"thread_count": thread_sub_query, "post_count": post_sub_query})
        return query_set.all()

    def get_private_forums_of_category(self, category, user):
        return self.filter(category=category, group__in=user.groups.all())\
            .order_by('position_in_category')\
            .select_related("category").distinct().all()


class TopicManager(models.Manager):
    """
    Custom topic manager.
    """

    def last_topics_of_a_member(self, author, user):
        """
        Gets last topics of a member but exclude all topics not accessible
        for the request user.
        :param author: Author of topics.
        :param user: Request user.
        :return: List of topics.
        """
        return self.filter(author=author) \
                   .exclude(Q(forum__group__isnull=False) & ~Q(forum__group__in=user.groups.all())) \
                   .prefetch_related("author") \
                   .order_by("-pubdate") \
                   .all()[:settings.ZDS_APP['forum']['home_number']]

    def get_beta_topic_of(self, tutorial):
        return self.filter(key=tutorial.pk, key__isnull=False).first()

    def get_last_topics(self):
        """
        Get last posted topics and prefetch some related properties.
        Depends on settings.ZDS_APP['topic']['home_number']
        :return:
        :rtype: django.models.Queryset
        """
        return self.order_by('-pubdate') \
                   .exclude(Q(forum__group__isnull=False)) \
                   .exclude(is_locked=True) \
                   .select_related('forum', 'author', 'last_message') \
                   .prefetch_related('tags').all()[:settings.ZDS_APP['topic']['home_number']]

    def get_all_topics_of_a_forum(self, forum_pk, is_sticky=False):
        return self.filter(forum__pk=forum_pk, is_sticky=is_sticky) \
            .order_by('-last_message__pubdate')\
            .select_related('author__profile')\
            .prefetch_related('last_message', 'tags').all()

    def get_all_topics_of_a_user(self, current, target):
        return self.filter(author=target)\
            .exclude(Q(forum__group__isnull=False) & ~Q(forum__group__in=current.groups.all()))\
            .prefetch_related("author")\
            .order_by("-pubdate").all()

    def get_all_topics_of_a_tag(self, tag, user):
        return self.filter(tags__in=[tag])\
            .order_by("-last_message__pubdate")\
            .prefetch_related('author', 'last_message', 'tags')\
            .exclude(Q(forum__group__isnull=False) & ~Q(forum__group__in=user.groups.all()))\
            .all()


class PostManager(InheritanceManager):
    """
    Custom post manager.
    """

    def get_messages_of_a_topic(self, topic_pk):
        return self.filter(topic__pk=topic_pk)\
            .select_related("author__profile")\
            .prefetch_related('alerts')\
            .prefetch_related('alerts__author')\
            .prefetch_related('alerts__author__profile')\
            .order_by("position").all()

    def get_all_messages_of_a_user(self, current, target):
        if current.has_perm("forum.change_post"):
            return self.filter(author=target)\
                .exclude(Q(topic__forum__group__isnull=False) & ~Q(topic__forum__group__in=current.groups.all()))\
                .prefetch_related("author")\
                .order_by("-pubdate").all()
        return self.filter(author=target)\
            .filter(is_visible=True)\
            .exclude(Q(topic__forum__group__isnull=False) & ~Q(topic__forum__group__in=current.groups.all()))\
            .prefetch_related("author")\
            .order_by("-pubdate").all()


class TopicReadManager(models.Manager):

    def topic_read_by_user(self, user, topic_sub_list=None):
        """ get all the topic that the user has already read.

        :param user: an authenticated user
        :param topic_sub_list: optional list of topics. If not ``None`` no subject out of this list will be selected
        :type topic_sub_list: list
        :return: the queryset over the already read topics
        :rtype: QuerySet
        """
        base_query_set = self.filter(user__pk=user.pk)
        if topic_sub_list is not None:
            base_query_set = base_query_set.filter(topic__in=topic_sub_list)
        base_query_set = base_query_set.filter(post=F("topic__last_message"))

        return base_query_set

    def list_read_topic_pk(self, user, topic_sub_list=None):
        """ get all the topic that the user has already read in a flat list.

        :param user: an authenticated user
        :param topic_sub_list: optional list of topics. If not ``None`` no subject out of this list will be selected
        :type topic_sub_list: list
        :return: the flat list of all topics primary key
        :rtype: list
        """
        return self.topic_read_by_user(user, topic_sub_list).values_list('topic__pk', flat=True)
