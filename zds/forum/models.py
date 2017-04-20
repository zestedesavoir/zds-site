# coding: utf-8
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
import logging
from datetime import datetime, timedelta
from math import ceil

from django.conf import settings
from django.contrib.auth.models import Group, User, AnonymousUser
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete

from elasticsearch_dsl.field import Text, Keyword, Integer, Boolean, Float, Date

from zds.forum.managers import TopicManager, ForumManager, PostManager, TopicReadManager
from zds.notification import signals
from zds.settings import ZDS_APP
from zds.searchv2.models import AbstractESDjangoIndexable, delete_document_in_elasticsearch, ESIndexManager
from zds.utils import get_current_user, slugify
from zds.utils.models import Comment, Tag


def sub_tag(tag):
    start = tag.group('start')
    end = tag.group('end')
    return u'{0}'.format(start + end)


@python_2_unicode_compatible
class Category(models.Model):
    """
    A Category is a simple container for Forums.
    There is no kind of logic in a Category. It simply here for Forum presentation in a predefined order.
    """
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['position', 'title']

    title = models.CharField('Titre', max_length=80)
    position = models.IntegerField('Position', default=0)
    # Some category slugs are forbidden due to path collisions: Category path is `/forums/<slug>` but some actions on
    # forums have path like `/forums/<action_name>`. Forbidden slugs are all top-level path in forum's `url.py` module.
    # As Categories can only be managed by superadmin, this is purely declarative and there is no control on slug.
    slug = models.SlugField(max_length=80,
                            unique=True,
                            help_text='Ces slugs vont provoquer des conflits '
                            "d'URL et sont donc interdits : notifications "
                            'resolution_alerte sujet sujets message messages')

    def __str__(self):
        """Textual form of a category."""
        return self.title

    def get_absolute_url(self):
        return reverse('cat-forums-list', kwargs={'slug': self.slug})

    def get_forums(self, user, with_count=False):
        """get all forums that user can access

        :param user: the related user
        :type user: User
        :param with_count: If true will preload thread and post number for each forum of this category
        :type with_count: bool
        :return: All forums in category, ordered by forum's position in category
        :rtype: list[Forum]
        """
        forums_pub = Forum.objects.get_public_forums_of_category(self, with_count=with_count)
        if user is not None and user.is_authenticated():
            forums_private = Forum.objects.get_private_forums_of_category(self, user)
            return list(forums_pub | forums_private)
        return forums_pub


@python_2_unicode_compatible
class Forum(models.Model):
    """
    A Forum, containing Topics. It can be public or restricted to some groups.
    """
    class Meta:
        verbose_name = 'Forum'
        verbose_name_plural = 'Forums'
        ordering = ['position_in_category', 'title']

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous-titre', max_length=200)

    # Groups authorized to read this forum. If no group is defined, the forum is public (and anyone can read it).
    groups = models.ManyToManyField(
        Group,
        verbose_name='Groupes autorisés (aucun = public)',
        blank=True)

    category = models.ForeignKey(Category, db_index=True, verbose_name='Catégorie')
    position_in_category = models.IntegerField('Position dans la catégorie',
                                               null=True, blank=True, db_index=True)

    slug = models.SlugField(max_length=80, unique=True)
    _nb_group = None
    objects = ForumManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('forum-topics-list', kwargs={'cat_slug': self.category.slug, 'forum_slug': self.slug})

    def get_topic_count(self):
        """Retrieve or agregate the number of threads in this forum. If this number already exists, it must be stored \
        in thread_count. Otherwise it will process a SQL query

        :return: the number of threads in the forum.
        """
        try:
            return self.thread_count
        except AttributeError:
            return Topic.objects.filter(forum=self).count()

    def get_post_count(self):
        """Retrieve or agregate the number of posts in this forum. If this number already exists, it must be stored \
        in post_count. Otherwise it will process a SQL query

        :return: the number of posts for a forum.
        """
        try:
            return self.post_count
        except AttributeError:
            return Post.objects.filter(topic__forum=self).count()

    def get_last_message(self):
        """
        :return: the last message on the forum, if there are any.
        """
        try:
            return Post.objects.filter(topic__forum=self).order_by('-pubdate').all()[0]
        except IndexError:
            return None

    def can_read(self, user):
        """
        Checks if an user can read current forum.
        The forum can be read if:
        - The forum has no access restriction (= no group), or
        - the user is in our database and is part of the restricted group which is needed to access this forum
        :param user: the user to check the rights
        :return: `True` if the user can read this forum, `False` otherwise.
        """

        if not self.has_group:
            return True
        else:
            # authentication is the best way to be sure groups are available in the user object
            if user is not None:
                groups = list(user.groups.all()) if not isinstance(user, AnonymousUser) else []
                return Forum.objects.filter(
                    groups__in=groups,
                    pk=self.pk).exists()
            else:
                return False

    @property
    def has_group(self):
        """
        Checks if this forum belongs to at least one group

        :return: ``True`` if it belongs to at least one group
        :rtype: bool
        """
        if self._nb_group is None:
            self._nb_group = self.groups.count()
        return self._nb_group > 0


@python_2_unicode_compatible
class Topic(AbstractESDjangoIndexable):
    """
    A Topic is a thread of posts.
    A topic has several states, witch are all independent:
    - Solved: it was a question, and this question has been answered. The "solved" state is set at author's discretion.
    - Locked: none can write on a locked topic.
    - Sticky: sticky topics are displayed on top of topic lists (ex: on forum page).
    """
    objects_per_batch = 1000

    class Meta:
        verbose_name = 'Sujet'
        verbose_name_plural = 'Sujets'

    title = models.CharField('Titre', max_length=160)
    subtitle = models.CharField('Sous-titre', max_length=200, null=True,
                                blank=True)

    forum = models.ForeignKey(Forum, verbose_name='Forum', db_index=True)
    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='topics', db_index=True)
    last_message = models.ForeignKey('Post', null=True,
                                     related_name='last_message',
                                     verbose_name='Dernier message')
    pubdate = models.DateTimeField('Date de création', auto_now_add=True)
    update_index_date = models.DateTimeField(
        'Date de dernière modification pour la réindexation partielle',
        auto_now=True,
        db_index=True)

    is_solved = models.BooleanField('Est résolu', default=False, db_index=True)
    is_locked = models.BooleanField('Est verrouillé', default=False, db_index=True)
    is_sticky = models.BooleanField('Est en post-it', default=False, db_index=True)

    github_issue = models.PositiveIntegerField('Ticket GitHub', null=True, blank=True)

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Tags du forum',
        blank=True,
        db_index=True)

    objects = TopicManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('topic-posts-list', args=[self.pk, self.slug()])

    def slug(self):
        return slugify(self.title)

    def get_post_count(self):
        """
        :return: the number of posts in the topic.
        """
        return Post.objects.filter(topic__pk=self.pk).count()

    def get_last_post(self):
        """
        :return: the last post in the thread.
        """
        return self.last_message

    def get_last_answer(self):
        """
        Gets the last answer in this tread, if any.
        Note the first post is not considered as an answer, therefore a topic with a single post (the 1st one) will
        return `None`.
        :return: the last answer in the thread, if any.
        """
        last_post = self.get_last_post()

        if last_post == self.first_post():
            return None
        else:
            return last_post

    def first_post(self):
        """
        :return: the first post of a topic, written by topic's author.
        """
        # we need the author prefetching as this method is widely used in templating directly or with
        # all the mess arround last_answer and last_read message
        return Post.objects\
            .filter(topic=self)\
            .select_related('author')\
            .order_by('position')\
            .first()

    def add_tags(self, tag_collection):
        """
        Add all tags contained in `tag_collection` to this topic.
        If a tag is unknown, it is added to the system.
        :param tag_collection: A collection of tags.
        """
        for tag in tag_collection:
            try:
                current_tag, created = Tag.objects.get_or_create(title=tag.lower().strip())
                self.tags.add(current_tag)
            except ValueError as e:
                logging.getLogger('zds.forum').warn(e)

        self.save()

    def last_read_post(self):
        """
        Returns the last post the current user has read in this topic.
        If it has never read this topic, returns the first post.
        Used in "last read post" balloon (base.html line 91).
        :return: the last post the user has read.
        """
        try:
            return TopicRead.objects \
                            .select_related() \
                            .filter(topic__pk=self.pk,
                                    user__pk=get_current_user().pk) \
                            .latest('post__position').post
        except TopicRead.DoesNotExist:
            return self.first_post()

    def resolve_last_read_post_absolute_url(self):
        """resolve the url that leads to the last post the current user has read. If current user is \
        anonymous, just lead to the thread start.

        :return: the url
        :rtype: str
        """
        user = get_current_user()
        if user is None or not user.is_authenticated():
            return self.first_unread_post().get_absolute_url()
        else:
            try:
                pk, pos = self.resolve_last_post_pk_and_pos_read_by_user(user)
                page_nb = 1
                if pos > ZDS_APP['forum']['posts_per_page']:
                    page_nb += (pos - 1) // ZDS_APP['forum']['posts_per_page']
                return '{}?page={}#p{}'.format(
                    self.get_absolute_url(), page_nb, pk)
            except TopicRead.DoesNotExist:
                return self.first_unread_post().get_absolute_url()

    def resolve_last_post_pk_and_pos_read_by_user(self, user):
        """get the primary key and position of the last post the user read

        :param user: the current (authenticated) user. Please do not try with unauthenticated user, il would lead to a \
        useless request.
        :return: the primary key
        :rtype: int
        """
        t_read = TopicRead.objects\
                          .select_related('post')\
                          .filter(topic__pk=self.pk,
                                  user__pk=user.pk) \
                          .latest('post__position')
        if t_read:
            return t_read.post.pk, t_read.post.position
        return Post.objects\
            .filter(topic__pk=self.pk)\
            .order_by('position')\
            .values('pk', 'position').first().values()

    def first_unread_post(self, user=None):
        """
        Returns the first post of this topics the current user has never read, or the first post if it has never read \
        this topic.\
        Used in notification menu.

        :return: The first unread post for this topic and this user.
        """
        try:
            if user is None:
                user = get_current_user()

            last_post = TopicRead.objects \
                                 .filter(topic__pk=self.pk,
                                         user__pk=user.pk) \
                                 .latest('post__position').post

            next_post = Post.objects.filter(topic__pk=self.pk,
                                            position__gt=last_post.position) \
                                    .select_related('author').first()
            return next_post
        except (TopicRead.DoesNotExist, Post.DoesNotExist):
            return self.first_post()

    def antispam(self, user=None):
        """
        Check if the user is allowed to post in a topic according to the `ZDS_APP['forum']['spam_limit_seconds']` value.
        The user can always post if someone else has posted last.
        If the user is the last poster and there is less than `ZDS_APP['forum']['spam_limit_seconds']` since the last
        post, the anti-spam is active and the user cannot post.
        :param user: An user. If undefined, the current user is used.
        :return: `True` if the anti-spam is active (user can't post), `False` otherwise.
        """
        if user is None:
            user = get_current_user()

        last_user_post = Post.objects\
            .filter(topic=self)\
            .filter(author=user.pk)\
            .order_by('position')\
            .last()

        if last_user_post and last_user_post == self.get_last_post():
            duration = datetime.now() - last_user_post.pubdate
            if duration.total_seconds() < settings.ZDS_APP['forum']['spam_limit_seconds']:
                return True

        return False

    def old_post_warning(self):
        """
        Check if the last message was written a long time ago according to `ZDS_APP['forum']['old_post_limit_days']`
        value.

        :return: `True` if the post is old (users are warned), `False` otherwise.
        """
        last_post = self.last_message

        if last_post is not None:
            t = last_post.pubdate + timedelta(days=settings.ZDS_APP['forum']['old_post_limit_days'])
            if t < datetime.today():
                return True

        return False

    @classmethod
    def get_es_mapping(cls):
        es_mapping = super(Topic, cls).get_es_mapping()

        es_mapping.field('title', Text(boost=1.5))
        es_mapping.field('tags', Text(boost=2.0))
        es_mapping.field('subtitle', Text())
        es_mapping.field('is_solved', Boolean())
        es_mapping.field('is_locked', Boolean())
        es_mapping.field('is_sticky', Boolean())
        es_mapping.field('pubdate', Date())
        es_mapping.field('forum_pk', Integer())

        # not indexed:
        es_mapping.field('get_absolute_url', Keyword(index=False))
        es_mapping.field('forum_title', Text(index=False))
        es_mapping.field('forum_get_absolute_url', Keyword(index=False))

        return es_mapping

    @classmethod
    def get_es_django_indexable(cls, force_reindexing=False):
        """Overridden to prefetch tags and forum
        """

        query = super(Topic, cls).get_es_django_indexable(force_reindexing)
        return query.prefetch_related('tags').select_related('forum')

    def get_es_document_source(self, excluded_fields=None):
        """Overridden to handle the case of tags (M2M field)
        """

        excluded_fields = excluded_fields or []
        excluded_fields.extend(['tags', 'forum_pk', 'forum_title', 'forum_get_absolute_url'])

        data = super(Topic, self).get_es_document_source(excluded_fields=excluded_fields)
        data['tags'] = [tag.title for tag in self.tags.all()]
        data['forum_pk'] = self.forum.pk
        data['forum_title'] = self.forum.title
        data['forum_get_absolute_url'] = self.forum.get_absolute_url()

        return data

    def save(self, *args, **kwargs):
        """Overridden to handle the displacement of the topic to another forum
        """

        try:
            old_self = Topic.objects.get(pk=self.pk)
        except Topic.DoesNotExist:
            pass
        else:
            if old_self.forum.pk != self.forum.pk or old_self.title != self.title:
                Post.objects.filter(topic__pk=self.pk).update(es_flagged=True)

        return super(Topic, self).save(*args, **kwargs)


@receiver(pre_delete, sender=Topic)
def delete_topic_in_elasticsearch(sender, instance, **kwargs):
    """catch the pre_delete signal to ensure the deletion in ES"""
    return delete_document_in_elasticsearch(instance)


@python_2_unicode_compatible
class Post(Comment, AbstractESDjangoIndexable):
    """
    A forum post written by an user.
    A post can be marked as useful: topic's author (or admin) can declare any topic as "useful", and this post is
    displayed as is on front.
    """
    objects_per_batch = 2000

    topic = models.ForeignKey(Topic, verbose_name='Sujet', db_index=True)

    is_useful = models.BooleanField('Est utile', default=False)
    objects = PostManager()

    def __str__(self):
        return "<Post pour '{0}', #{1}>".format(self.topic, self.pk)

    def get_absolute_url(self):
        """
        :return: the absolute URL for this post, including page in the topic.
        """
        page = int(ceil(float(self.position) / settings.ZDS_APP['forum']['posts_per_page']))

        return '{0}?page={1}#p{2}'.format(
            self.topic.get_absolute_url(),
            page,
            self.pk)

    def get_notification_title(self):
        return self.topic.title

    @classmethod
    def get_es_mapping(cls):
        es_mapping = super(Post, cls).get_es_mapping()

        es_mapping.field('text_html', Text())
        es_mapping.field('is_useful', Boolean())
        es_mapping.field('is_visible', Boolean())
        es_mapping.field('position', Integer())
        es_mapping.field('like_dislike_ratio', Float())
        es_mapping.field('pubdate', Date())
        es_mapping.field('forum_pk', Integer())
        es_mapping.field('topic_pk', Integer())

        # not indexed:
        es_mapping.field('get_absolute_url', Keyword(index=False))
        es_mapping.field('topic_title', Text(index=False))
        es_mapping.field('forum_title', Text(index=False))
        es_mapping.field('forum_get_absolute_url', Keyword(index=False))

        return es_mapping

    @classmethod
    def get_es_django_indexable(cls, force_reindexing=False):
        """Overridden to prefetch stuffs
        """

        q = super(Post, cls).get_es_django_indexable(force_reindexing)\
            .prefetch_related('topic')\
            .prefetch_related('topic__forum')

        return q

    def get_es_document_source(self, excluded_fields=None):
        """Overridden to handle the information of the topic
        """

        excluded_fields = excluded_fields or []
        excluded_fields.extend(
            ['like_dislike_ratio', 'topic_title', 'topic_pk', 'forum_title', 'forum_pk', 'forum_get_absolute_url'])

        data = super(Post, self).get_es_document_source(excluded_fields=excluded_fields)

        data['like_dislike_ratio'] = \
            (self.like / self.dislike) if self.dislike != 0 else self.like if self.like != 0 else 1

        data['topic_pk'] = self.topic.pk
        data['topic_title'] = self.topic.title

        data['forum_pk'] = self.topic.forum.pk
        data['forum_title'] = self.topic.forum.title
        data['forum_get_absolute_url'] = self.topic.forum.get_absolute_url()

        return data

    def hide_comment_by_user(self, user, text_hidden):
        """Overridden to directly hide the post in ES as well
        """

        super(Post, self).hide_comment_by_user(user, text_hidden)

        index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)
        index_manager.update_single_document(self, {'is_visible': False})


@receiver(pre_delete, sender=Post)
def delete_post_in_elasticsearch(sender, instance, **kwargs):
    """catch the pre_delete signal to ensure the deletion in ES"""
    return delete_document_in_elasticsearch(instance)


@python_2_unicode_compatible
class TopicRead(models.Model):
    """
    This model tracks the last post read in a topic by a user.
    Technically it is a simple joint [user, topic, last read post].
    """
    class Meta:
        verbose_name = 'Sujet lu'
        verbose_name_plural = 'Sujets lus'
        unique_together = ('topic', 'user')

    topic = models.ForeignKey(Topic, db_index=True)
    post = models.ForeignKey(Post, db_index=True)
    user = models.ForeignKey(User, related_name='topics_read', db_index=True)
    objects = TopicReadManager()

    def __str__(self):
        return "<Sujet '{0}' lu par {1}, #{2}>".format(self.topic,
                                                       self.user,
                                                       self.post.pk)


def is_read(topic, user=None):
    """
    Checks if the user has read the **last post** of the topic.
    Returns false if the user read the topic except its last post.
    Technically this is done by checking if the user has a `TopicRead` object
    for the last post of this topic.
    :param topic: A topic
    :param user: A user. If undefined, the current user is used.
    :return:
    """
    if user is None:
        user = get_current_user()

    return TopicRead.objects.filter(post=topic.last_message, topic=topic, user=user).exists()


def mark_read(topic, user=None):
    """
    Mark the last message of a topic as read for the current user.
    :param topic: A topic.
    """
    if not user:
        user = get_current_user()

    if user and user.is_authenticated():
        current_topic_read = TopicRead.objects.filter(topic=topic, user=user).first()
        if current_topic_read is None:
            current_topic_read = TopicRead(post=topic.last_message, topic=topic, user=user)
        else:
            current_topic_read.post = topic.last_message
        current_topic_read.save()
        signals.content_read.send(sender=topic.__class__, instance=topic, user=user)
