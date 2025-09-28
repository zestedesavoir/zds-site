import logging
from datetime import datetime, timedelta
from math import ceil

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse

from zds.forum import signals
from zds.forum.managers import ForumManager, PostManager, TopicManager, TopicReadManager
from zds.search.models import AbstractSearchIndexableModel
from zds.search.utils import SearchFilter, SearchIndexManager, clean_html, date_to_timestamp_int
from zds.utils import get_current_user, old_slugify
from zds.utils.models import Comment, Tag


def get_search_filter_authorized_forums(user: User) -> SearchFilter:
    filter_by = SearchFilter()
    filter_by.add_exact_filter("forum_pk", Forum.objects.get_authorized_forums_pk(user))

    return filter_by


class ForumCategory(models.Model):
    """
    A ForumCategory is a simple container for Forums.
    There is no kind of logic in a ForumCategory. It simply here for Forum presentation in a predefined order.
    """

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["position", "title"]

    title = models.CharField("Titre", max_length=80)
    position = models.IntegerField("Position", default=0)
    # Some category slugs are forbidden due to path collisions: ForumCategory path is `/forums/<slug>` but some actions
    # on forums have path like `/forums/<action_name>`. Forbidden slugs are all top-level path in forum's `url.py`
    # module. As Categories can only be managed by superadmin, this is purely declarative and there is no control on
    # slug.
    slug = models.SlugField(
        max_length=80,
        unique=True,
        help_text="Ces slugs vont provoquer des conflits "
        "d'URL et sont donc interdits : notifications "
        "resolution_alerte sujet sujets message messages",
    )

    def __str__(self):
        """Textual form of a category."""
        return self.title

    def get_absolute_url(self):
        return reverse("forum:cat-forums-list", kwargs={"slug": self.slug})

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
        if user is not None and user.is_authenticated:
            forums_private = Forum.objects.get_private_forums_of_category(self, user)
            return list(forums_pub | forums_private)
        return forums_pub


class Forum(models.Model):
    """
    A Forum, containing Topics. It can be public or restricted to some groups.
    """

    class Meta:
        verbose_name = "Forum"
        verbose_name_plural = "Forums"
        ordering = ["position_in_category", "title"]

    title = models.CharField("Titre", max_length=80)
    subtitle = models.CharField("Sous-titre", max_length=200)

    # Groups authorized to read this forum. If no group is defined, the forum is public (and anyone can read it).
    groups = models.ManyToManyField(Group, verbose_name="Groupes autorisés (aucun = public)", blank=True)

    # better handling of on_delete with SET(value)?
    category = models.ForeignKey(ForumCategory, db_index=True, verbose_name="Catégorie", on_delete=models.CASCADE)
    position_in_category = models.IntegerField("Position dans la catégorie", null=True, blank=True, db_index=True)

    slug = models.SlugField(max_length=80, unique=True)
    _nb_group = None
    objects = ForumManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:topics-list", kwargs={"cat_slug": self.category.slug, "forum_slug": self.slug})

    def get_topic_count(self):
        """Retrieve or aggregate the number of threads in this forum. If this number already exists, it must be stored \
        in thread_count. Otherwise it will process a SQL query.

        :return: the number of threads in the forum.
        """
        try:
            return self.thread_count
        except AttributeError:
            return Topic.objects.filter(forum=self).count()

    def get_post_count(self):
        """Retrieve or aggregate the number of posts in this forum. If this number already exists, it must be stored \
        in post_count. Otherwise it will process a SQL query.

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
            last_post = Post.objects.select_related("topic").filter(topic__forum=self).order_by("-pubdate").all()[0]
            last_post.topic.forum = self
            return last_post
        except IndexError:
            return None

    def can_read(self, user):
        """
        Checks if a user can read current forum.
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
                return Forum.objects.filter(groups__in=groups, pk=self.pk).exists()
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


class Topic(AbstractSearchIndexableModel):
    """
    A Topic is a thread of posts.
    A topic has several states, witch are all independent:
    - Solved: it was a question, and this question has been answered. The "solved" state is set at author's discretion.
    - Locked: none can write on a locked topic.
    - Sticky: sticky topics are displayed on top of topic lists (ex: on forum page).
    """

    initial_search_index_batch_size = 256

    class Meta:
        verbose_name = "Sujet"
        verbose_name_plural = "Sujets"

    title = models.CharField("Titre", max_length=160)
    subtitle = models.CharField("Sous-titre", max_length=200, null=True, blank=True)

    # on_delete default forum?
    forum = models.ForeignKey(Forum, verbose_name="Forum", db_index=True, on_delete=models.CASCADE)
    # on_delete anonymous?
    author = models.ForeignKey(
        User, verbose_name="Auteur", related_name="topics", db_index=True, on_delete=models.CASCADE
    )
    last_message = models.ForeignKey(
        "Post", null=True, related_name="last_message", verbose_name="Dernier message", on_delete=models.SET_NULL
    )
    pubdate = models.DateTimeField("Date de création", auto_now_add=True)
    solved_by = models.ForeignKey(
        User,
        verbose_name="Utilisateur ayant noté le sujet comme résolu",
        db_index=True,
        default=None,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    is_locked = models.BooleanField("Est verrouillé", default=False, db_index=True)
    is_sticky = models.BooleanField("Est en post-it", default=False, db_index=True)
    github_issue = models.PositiveIntegerField("Ticket GitHub", null=True, blank=True)
    github_repository_name = models.CharField("Nom du dépôt GitHub", max_length=100, null=True, blank=True)

    tags = models.ManyToManyField(Tag, verbose_name="Tags du forum", blank=True, db_index=True)

    objects = TopicManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_user_post = dict()
        self._last_post = None
        self._first_post = None
        self._is_read = None

    def __str__(self):
        return self.title

    @property
    def is_solved(self):
        return self.solved_by is not None

    @property
    def meta_description(self):
        first_post = self.first_post()
        if len(first_post.text) < 120:
            return first_post.text
        return Topic.__remove_greetings(first_post)[: settings.ZDS_APP["forum"]["description_size"]]

    @staticmethod
    def __remove_greetings(post):
        greetings = settings.ZDS_APP["forum"]["greetings"]
        max_size = settings.ZDS_APP["forum"]["description_size"] + 1
        text = post.text
        for greeting in greetings:
            if text.strip().lower().startswith(greeting):
                index_of_dot = max(text.index("\n") if "\n" in text else -1, -1)
                index_of_dot = min(index_of_dot, text.index(".") if "." in text else max_size)
                index_of_dot = min(index_of_dot, text.index("!") if "!" in text else max_size)
                return text[index_of_dot + 1 :].strip()
        return text

    def get_absolute_url(self):
        return reverse("forum:topic-posts-list", args=[self.pk, self.slug()])

    def slug(self):
        return old_slugify(self.title)

    def get_post_count(self):
        """
        :return: the number of posts in the topic.
        """
        return Post.objects.filter(topic__pk=self.pk).count()

    def get_last_post(self):
        """
        :return: the last post in the thread.
        """
        if self._last_post is None:
            self._last_post = Post.objects.filter(pk=self.last_message).select_related("author").first()

        return self._last_post

    def get_last_answer(self):
        """
        Gets the last answer in this tread, if any.
        Note the first post is not considered as an answer, therefore a topic with a single post (the 1st one) will
        return `None`.
        :return: the last answer in the thread, if any.
        :rtype: Post
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
        if not self._first_post:
            # we need the author prefetching as this method is widely used in templating directly or with
            # all the mess around last_answer and last_read message
            self._first_post = Post.objects.filter(topic=self).select_related("author").order_by("position").first()
            self._first_post.topic = self
        return self._first_post

    def add_tags(self, tag_collection):
        """
        Add all tags contained in `tag_collection` to this topic.
        If a tag is unknown, it is added to the system.
        :param tag_collection: A collection of tags.
        """
        for tag in filter(None, tag_collection):
            try:
                current_tag, created = Tag.objects.get_or_create(title=tag.lower().strip())
                self.tags.add(current_tag)
            except ValueError as e:
                logging.getLogger(__name__).warning(e)

        self.save()
        signals.topic_edited.send(sender=self.__class__, topic=self)

    def last_read_post(self):
        """
        Returns the last post the current user has read in this topic.
        If it has never read this topic, returns the first post.
        Used in "last read post" balloon (base.html line 91).
        :return: the last post the user has read.
        """
        try:
            return (
                TopicRead.objects.select_related()
                .filter(topic__pk=self.pk, user__pk=get_current_user().pk)
                .latest("post__position")
                .post
            )
        except TopicRead.DoesNotExist:
            return self.first_post()

    def resolve_first_post_absolute_url(self):
        return self.first_post().get_absolute_url()

    def resolve_last_read_post_absolute_url(self):
        """resolve the url that leads to the last post the current user has read. If current user is \
        anonymous, just lead to the thread start.

        :return: the url
        :rtype: str
        """
        user = get_current_user()
        try:
            pk, pos = self.resolve_last_post_pk_and_pos_read_by_user(user)
            page_nb = 1
            if pos > settings.ZDS_APP["forum"]["posts_per_page"]:
                page_nb += (pos - 1) // settings.ZDS_APP["forum"]["posts_per_page"]
            return f"{self.get_absolute_url()}?page={page_nb}#p{pk}"
        except TopicRead.DoesNotExist:
            return self.first_post().get_absolute_url()

    def resolve_last_post_pk_and_pos_read_by_user(self, user):
        """get the primary key and position of the last post the user read

        :param user: the current (authenticated) user. Please do not try with unauthenticated user, il would lead to a \
        useless request.
        :return: the primary key
        :rtype: int
        """
        t_read = (
            TopicRead.objects.select_related("post")
            .filter(topic__pk=self.pk, user__pk=user.pk)
            .latest("post__position")
        )
        if t_read:
            return t_read.post.pk, t_read.post.position
        return list(
            Post.objects.filter(topic__pk=self.pk).order_by("position").values("pk", "position").first().values()
        )

    def first_unread_post(self, user: User = None):
        """
        Returns the first post of this topics the current user has never read, or the first post if it has never read \
        this topic.\
        Used in notification menu.

        :param user: The user who potentially has read a post. If ``None`` will get request user

        :return: The first unread post for this topic and this user. If the topic was read, gets ``last_post`` or None \
        if no posts was found after OP.
        """
        try:
            if user is None:
                user = get_current_user()

            last_post = TopicRead.objects.filter(topic__pk=self.pk, user__pk=user.pk).latest("post__position").post

            next_post = (
                Post.objects.filter(topic__pk=self.pk, position__gt=last_post.position).order_by("position").first()
            ) or self.get_last_answer()
            # if read was the last message, there is no next so default to last message
            return next_post
        except TopicRead.DoesNotExist:
            # if no read : the whole topic is not read so get first message
            return self.first_post()

    def antispam(self, user=None):
        """
        Check if the user is allowed to post in a topic according to the `ZDS_APP['forum']['spam_limit_seconds']` value.
        The user can always post if someone else has posted last.
        If the user is the last poster and there is less than `ZDS_APP['forum']['spam_limit_seconds']` since the last
        post, the anti-spam is active and the user cannot post.
        :param user: A user. If undefined, the current user is used.
        :return: `True` if the anti-spam is active (user can't post), `False` otherwise.
        """
        if user is None:
            user = get_current_user()

        if user not in self._last_user_post:
            self._last_user_post[user] = (
                Post.objects.filter(topic=self).filter(author=user.pk).order_by("position").last()
            )
        last_user_post = self._last_user_post[user]

        if last_user_post and last_user_post == self.get_last_post():
            duration = datetime.now() - last_user_post.pubdate
            if duration.total_seconds() < settings.ZDS_APP["forum"]["spam_limit_seconds"]:
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
            t = last_post.pubdate + timedelta(days=settings.ZDS_APP["forum"]["old_post_limit_days"])
            if t < datetime.today():
                return True

        return False

    @property
    def is_read(self):
        if self._is_read is None:
            self._is_read = self.is_read_by_user(get_current_user())
        return self._is_read

    def is_read_by_user(self, user=None, check_auth=True):
        return TopicRead.objects.is_topic_last_message_read(self, user, check_auth)

    @classmethod
    def get_search_document_schema(cls):
        search_engine_schema = super().get_search_document_schema()

        search_engine_schema["fields"] = [
            {"name": "forum_pk", "type": "int32", "facet": False},  # we can filter on it
            {"name": "title", "type": "string"},  # we search on it
            {"name": "subtitle", "type": "string", "optional": True},  # we search on it
            {"name": "forum_title", "type": "string", "index": False},
            {"name": "tags", "type": "string[]", "facet": True},  # we search on it
            {"name": "tag_slugs", "type": "string[]", "optional": True, "index": False},
            {"name": "pubdate", "type": "int64", "index": False},
            {"name": "get_absolute_url", "type": "string", "index": False},
            {"name": "forum_get_absolute_url", "type": "string", "index": False},
            {"name": "weight", "type": "float"},  # we sort on it
        ]

        return search_engine_schema

    @classmethod
    def get_indexable_objects(cls, force_reindexing=False):
        """Overridden to prefetch tags and forum"""

        query = super().get_indexable_objects(force_reindexing)
        return query.prefetch_related("tags").select_related("forum")

    def get_document_source(self, excluded_fields=[]):
        excluded_fields.extend(["tags", "pubdate"])

        data = super().get_document_source(excluded_fields=excluded_fields)
        data["tags"] = []
        data["tag_slugs"] = []
        for tag in self.tags.all():
            data["tags"].append(tag.title)
            data["tag_slugs"].append(tag.slug)  # store also slugs to have them from search results
        data["forum_pk"] = self.forum.pk
        data["forum_title"] = self.forum.title
        data["forum_get_absolute_url"] = self.forum.get_absolute_url()
        data["pubdate"] = date_to_timestamp_int(self.pubdate)
        data["weight"] = self._get_search_weight()

        return data

    @classmethod
    def get_search_query(cls, user):
        return {
            "query_by": "title,subtitle,tags",
            "query_by_weights": "{},{},{}".format(
                settings.ZDS_APP["search"]["boosts"]["topic"]["title"],
                settings.ZDS_APP["search"]["boosts"]["topic"]["subtitle"],
                settings.ZDS_APP["search"]["boosts"]["topic"]["tags"],
            ),
            "filter_by": str(get_search_filter_authorized_forums(user)),
            "sort_by": "weight:desc",
        }

    def save(self, *args, **kwargs):
        """Overridden to handle the displacement of the topic to another forum"""

        try:
            old_self = Topic.objects.get(pk=self.pk)
        except Topic.DoesNotExist:
            pass
        else:
            is_moved = old_self.forum.pk != self.forum.pk
            posts = Post.objects.filter(topic__pk=self.pk)
            if is_moved or old_self.title != self.title:
                posts.update(search_engine_requires_index=True)

            if is_moved and self.forum.groups is not None:
                # Moved to a restricted forum, we remove it from the search
                # engine, will be correctly reindexed later (this approach is
                # simpler than updating everything in the search engine)
                search_engine_manager = SearchIndexManager()

                filter_by = SearchFilter()
                filter_by.add_exact_filter("topic_pk", [self.pk])

                search_engine_manager.delete_by_query(Post.get_search_document_type(), {"filter_by": str(filter_by)})
                # The topic may not exist in the search engine yet, if it was not yet indexed
                search_engine_manager.delete_document(self)

        return super().save(*args, **kwargs)

    def _get_search_weight(self):
        """
        This function calculates a weight for topics in order to sort them according to different boosts.
        There is a boost according to the state of the topic:
        - Solved: it was a question, and this question has been answered. The "solved" state is set at author's discretion.
        - Locked: nobody can write on a locked topic.
        - Sticky: sticky topics are displayed on top of topic lists (ex: on forum page).
        """
        weight_solved = settings.ZDS_APP["search"]["boosts"]["topic"]["if_solved"]
        weight_sticky = settings.ZDS_APP["search"]["boosts"]["topic"]["if_sticky"]
        weight_locked = settings.ZDS_APP["search"]["boosts"]["topic"]["if_locked"]
        weight_global = settings.ZDS_APP["search"]["boosts"]["topic"]["global"]
        # if the topic isn't in one of this states (solved, locked, sticky), it needs a weight, it's the global weight
        is_global = 0 if self.is_solved or self.is_sticky or self.is_locked else 1
        return max(
            weight_solved * self.is_solved,
            weight_sticky * self.is_sticky,
            weight_locked * self.is_locked,
            is_global * weight_global,
        )


@receiver(post_save, sender=Tag)
def topic_tags_changed(instance, created, **kwargs):
    if not created:
        # It is an update of an existing object
        Topic.objects.filter(tags=instance.pk).update(search_engine_requires_index=True)


@receiver(post_save, sender=Forum)
def forum_title_changed(instance, created, **kwargs):
    if not created:
        # It is an update of an existing object
        Topic.objects.filter(forum=instance.pk).update(search_engine_requires_index=True)
        Post.objects.filter(topic__forum=instance.pk).update(search_engine_requires_index=True)


class Post(Comment, AbstractSearchIndexableModel):
    """
    A forum post written by a user.
    A post can be marked as useful: topic's author (or admin) can declare any topic as "useful", and this post is
    displayed as is on front.
    """

    initial_search_index_batch_size = 512

    topic = models.ForeignKey(Topic, verbose_name="Sujet", db_index=True, on_delete=models.CASCADE)

    is_useful = models.BooleanField("Est utile", default=False)
    objects = PostManager()

    def __str__(self):
        return f"<Post pour '{self.topic}', #{self.pk}>"

    def get_absolute_url(self):
        """
        :return: the absolute URL for this post, including page in the topic.
        """
        page = int(ceil(float(self.position) / settings.ZDS_APP["forum"]["posts_per_page"]))

        return f"{self.topic.get_absolute_url()}?page={page}#p{self.pk}"

    def get_notification_title(self):
        return self.topic.title

    @classmethod
    def get_search_document_schema(cls):
        search_engine_schema = super().get_search_document_schema()

        search_engine_schema["fields"] = [
            {"name": "topic_pk", "type": "int64"},  # we filter on it when a topic is moved
            {"name": "forum_pk", "type": "int64"},  # we can filter on it
            {"name": "topic_title", "type": "string", "index": False},
            {"name": "forum_title", "type": "string", "index": False},
            {"name": "text", "type": "string"},  # we search on it
            {"name": "pubdate", "type": "int64", "index": False},
            {"name": "get_absolute_url", "type": "string", "index": False},
            {"name": "forum_get_absolute_url", "type": "string", "index": False},
            {"name": "weight", "type": "float", "facet": False},  # we sort on it
        ]

        return search_engine_schema

    @classmethod
    def get_indexable_objects(cls, force_reindexing=False):
        """Overridden to prefetch stuffs"""

        q = (
            super()
            .get_indexable_objects(force_reindexing)
            .filter(is_visible=True)
            .prefetch_related("topic")
            .prefetch_related("topic__forum")
        )

        return q

    def get_document_source(self, excluded_fields=[]):
        """Overridden to handle the information of the topic"""

        excluded_fields.extend(["pubdate", "text"])

        data = super().get_document_source(excluded_fields=excluded_fields)
        data["topic_pk"] = self.topic.pk
        data["topic_title"] = self.topic.title
        data["forum_pk"] = self.topic.forum.pk
        data["forum_title"] = self.topic.forum.title
        data["forum_get_absolute_url"] = self.topic.forum.get_absolute_url()
        data["pubdate"] = date_to_timestamp_int(self.pubdate)
        data["text"] = clean_html(self.text_html)
        data["weight"] = self._get_search_weight()

        return data

    def hide_comment_by_user(self, user, text_hidden):
        """Overridden to directly delete the post in the search engine as well"""

        super().hide_comment_by_user(user, text_hidden)

        search_engine_manager = SearchIndexManager()
        search_engine_manager.delete_document(self)

    def _get_search_weight(self):
        """
        This function calculates a weight for post in order to sort them according to different boosts.
        There is a boost according to the position, the usefulness and the ration of likes.
        """
        weight_first = settings.ZDS_APP["search"]["boosts"]["post"]["if_first"]
        weight_useful = settings.ZDS_APP["search"]["boosts"]["post"]["if_useful"]
        weight_ld_ratio_above_1 = settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_above_1"]
        weight_ld_ratio_below_1 = settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_below_1"]
        weight_global = settings.ZDS_APP["search"]["boosts"]["post"]["global"]

        like_dislike_ratio = (self.like / self.dislike) if self.dislike != 0 else self.like if self.like != 0 else 1
        is_ratio_above_1 = 1 if like_dislike_ratio >= 1 else 0
        is_ratio_below_1 = 1 - is_ratio_above_1

        is_first = 1 if self.position == 1 else 0

        return max(
            weight_first * is_first,
            weight_useful * self.is_useful,
            weight_ld_ratio_above_1 * is_ratio_above_1,
            weight_ld_ratio_below_1 * is_ratio_below_1,
            weight_global,
        )

    @classmethod
    def get_search_query(cls, user):
        filter_by = get_search_filter_authorized_forums(user)

        return {
            "query_by": "text",
            "query_by_weights": "{}".format(
                settings.ZDS_APP["search"]["boosts"]["post"]["text"],
            ),
            "filter_by": str(filter_by),
            "sort_by": "weight:desc",
        }


@receiver(pre_delete, sender=Topic)
@receiver(pre_delete, sender=Post)
def delete_in_search(sender, instance, **kwargs):
    """catch the pre_delete signal to ensure the deletion in the search engine"""
    SearchIndexManager().delete_document(instance)


class TopicRead(models.Model):
    """
    This model tracks the last post read in a topic by a user.
    Technically it is a simple joint [user, topic, last read post].
    """

    class Meta:
        verbose_name = "Sujet lu"
        verbose_name_plural = "Sujets lus"
        unique_together = ("topic", "user")

    topic = models.ForeignKey(Topic, db_index=True, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="topics_read", db_index=True, on_delete=models.CASCADE)
    objects = TopicReadManager()

    def __str__(self):
        return f"<Sujet '{self.topic}' lu par {self.user}, #{self.post.pk}>"


def mark_read(topic, user=None):
    """
    Mark the last message of a topic as read for the current user.
    :param topic: A topic.
    """
    if not user:
        user = get_current_user()

    if user and user.is_authenticated:
        current_topic_read = TopicRead.objects.filter(topic=topic, user=user).first()
        if current_topic_read is None:
            current_topic_read = TopicRead(post=topic.last_message, topic=topic, user=user)
        else:
            current_topic_read.post = topic.last_message
        current_topic_read.save()
        signals.topic_read.send(sender=topic.__class__, instance=topic, user=user)
