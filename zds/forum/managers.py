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
        queryset = self.filter(category=category, groups__isnull=True).select_related('category').distinct()
        if with_count:
            # this request count the threads in each forum
            thread_sub_query = 'SELECT COUNT(*) FROM forum_topic WHERE forum_topic.forum_id=forum_forum.id'
            # this request count the posts in each forum
            post_sub_query = 'SELECT COUNT(*) FROM forum_post WHERE forum_post.topic_id ' \
                             'IN(SELECT id FROM forum_topic WHERE forum_topic.forum_id=forum_forum.id)'

            queryset = queryset.extra(select={'thread_count': thread_sub_query, 'post_count': post_sub_query})
        return queryset.all()

    def get_private_forums_of_category(self, category, user):
        return self.filter(category=category, groups__in=user.groups.all())\
            .order_by('position_in_category')\
            .select_related('category').distinct().all()


class TopicManager(models.Manager):
    """
    Custom topic manager.
    """

    def visibility_check_query(self, current_user):
        """
        Build a subquery that checks if a topic is readable by current user
        :param current_user:
        :return:
        """
        if current_user.is_authenticated():
            return Q(forum__groups__isnull=True) | Q(forum__groups__pk__in=current_user.profile.group_pks)
        else:
            return Q(forum__groups__isnull=True)

    def last_topics_of_a_member(self, author, user):
        """
        Gets last topics of a member but exclude all topics not accessible
        for the request user.
        :param author: Author of topics.
        :param user: Request user.
        :return: List of topics.
        """
        queryset = self.filter(author=author) \
                       .prefetch_related('author')
        queryset = queryset.filter(self.visibility_check_query(user)).distinct()

        return queryset.order_by('-pubdate').all()[:settings.ZDS_APP['forum']['home_number']]

    def get_beta_topic_of(self, tutorial):
        return self.filter(key=tutorial.pk, key__isnull=False).first()

    def get_last_topics(self):
        """
        Get last posted topics and prefetch some related properties.
        Depends on settings.ZDS_APP['topic']['home_number']
        :return:
        :rtype: django.models.Queryset
        """
        return self.filter(is_locked=False, forum__groups__isnull=True) \
                   .select_related('forum', 'author', 'last_message') \
                   .prefetch_related('tags').order_by('-pubdate') \
                   .all()[:settings.ZDS_APP['topic']['home_number']]

    def get_all_topics_of_a_forum(self, forum_pk, is_sticky=False):
        return self.filter(forum__pk=forum_pk, is_sticky=is_sticky) \
                   .order_by('-last_message__pubdate')\
                   .select_related('author__profile')\
                   .prefetch_related('last_message', 'tags').all()

    def get_all_topics_of_a_user(self, current, target):
        queryset = self.filter(author=target)\
                       .prefetch_related('author')
        queryset = queryset.filter(self.visibility_check_query(current)).distinct()
        return queryset.order_by('-pubdate').all()

    def get_all_topics_of_a_tag(self, tag, user):
        queryset = self.filter(tags__in=[tag])\
                       .prefetch_related('author', 'last_message', 'tags')
        queryset = queryset.filter(self.visibility_check_query(user)).distinct()
        return queryset.order_by('-last_message__pubdate')


class PostManager(InheritanceManager):
    """
    Custom post manager.
    """

    def visibility_check_query(self, current_user):
        """
        Build a subquery that checks if a post is readable by current user
        :param current_user:
        :return:
        """
        if current_user.is_authenticated():
            return Q(topic__forum__groups__isnull=True) | Q(topic__forum__groups__pk__in=current_user.profile.group_pks)
        return Q(topic__forum__groups__isnull=True)

    def get_messages_of_a_topic(self, topic_pk):
        return self.filter(topic__pk=topic_pk)\
                   .select_related('hat')\
                   .select_related('author__profile')\
                   .prefetch_related('alerts_on_this_comment')\
                   .prefetch_related('alerts_on_this_comment__author')\
                   .prefetch_related('alerts_on_this_comment__author__profile')\
                   .order_by('position').all()

    def get_all_messages_of_a_user(self, current, target):
        queryset = self.filter(author=target).distinct()

        # if user can't change posts, exclude hidden messages from queryset
        if not current.has_perm('forum.change_post'):
            queryset = queryset.filter(is_visible=True)

        queryset = queryset\
            .filter(self.visibility_check_query(current))\
            .prefetch_related('author')\
            .order_by('-pubdate')

        return queryset


class TopicReadManager(models.Manager):

    def topic_read_by_user(self, user, topic_sub_list=None):
        """ get all the topic that the user has already read.

        :param user: an authenticated user
        :param topic_sub_list: optional list of topics. If not ``None`` no subject out of this list will be selected
        :type topic_sub_list: list
        :return: the queryset over the already read topics
        :rtype: QuerySet
        """
        base_queryset = self.filter(user__pk=user.pk)
        if topic_sub_list is not None:
            base_queryset = base_queryset.filter(topic__in=topic_sub_list)
        base_queryset = base_queryset.filter(post=F('topic__last_message'))

        return base_queryset

    def list_read_topic_pk(self, user, topic_sub_list=None):
        """ get all the topic that the user has already read in a flat list.

        :param user: an authenticated user
        :param topic_sub_list: optional list of topics. If not ``None`` no subject out of this list will be selected
        :type topic_sub_list: list
        :return: the flat list of all topics primary key
        :rtype: list
        """
        return self.topic_read_by_user(user, topic_sub_list).values_list('topic__pk', flat=True)
