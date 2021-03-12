from math import ceil

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models

from zds.mp.managers import PrivateTopicManager, PrivatePostManager
from zds.mp import signals
from zds.utils import get_current_user, old_slugify


class NotReachableError(Exception):
    """Raised when a user cannot be reached using private messages (e.g. bots)."""

    pass


class NotParticipatingError(Exception):
    """Raised when trying to perform an operation requiring the user to be a participant."""


def is_reachable(user):
    """
    Check if a user is reachable. Unreachable users are unable to read replies to their messages (e.g. bots).

    :param user: a given user
    :return: True if the user is reachable, False otherwise.
    """
    user_group_names = [g.name for g in user.groups.all()]
    return settings.ZDS_APP["member"]["bot_group"] not in user_group_names


class PrivateTopic(models.Model):
    """
    Private topic, containing private posts.

    We maintain the following invariants :
        * all participants are reachable,
        * no duplicate participant.

    A participant is either the author or a mere participant.
    """

    class Meta:
        verbose_name = "Message privé"
        verbose_name_plural = "Messages privés"

    title = models.CharField("Titre", max_length=130)
    subtitle = models.CharField("Sous-titre", max_length=200, blank=True)
    author = models.ForeignKey(
        User, verbose_name="Auteur", related_name="author", db_index=True, on_delete=models.SET_NULL, null=True
    )
    participants = models.ManyToManyField(User, verbose_name="Participants", related_name="participants", db_index=True)
    last_message = models.ForeignKey(
        "PrivatePost", null=True, related_name="last_message", verbose_name="Dernier message", on_delete=models.SET_NULL
    )
    pubdate = models.DateTimeField("Date de création", auto_now_add=True, db_index=True)
    objects = PrivateTopicManager()

    def __str__(self):
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
        return reverse("private-posts-list", args=[self.pk, self.slug()])

    def slug(self):
        """
        PrivateTopic doesn't have a slug attribute of a private topic. To be compatible
        with older private topic, the slug is always re-calculated when we need one.
        :return: title slugify.
        """
        return old_slugify(self.title)

    def get_post_count(self):
        """
        Get the number of private posts in a single PrivateTopic object.

        :return: number of posts in PrivateTopic object
        :rtype: int
        """
        return PrivatePost.objects.filter(privatetopic__pk=self.pk).count()

    def get_last_answer(self):
        """
        Get the last answer in the PrivateTopic written by topic's author, if exists.

        :return: PrivateTopic object last answer (PrivatePost)
        :rtype: PrivatePost object or None
        """
        last_post = PrivatePost.objects.filter(privatetopic__pk=self.pk).order_by("-position_in_topic").first()

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
        return PrivatePost.objects.filter(privatetopic=self).order_by("position_in_topic").first()

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
            post = PrivateTopicRead.objects.select_related().filter(privatetopic=self, user=user)
            if len(post) == 0:
                return self.first_post()
            return post.latest("privatepost__position_in_topic").privatepost

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
            last_post = (
                PrivateTopicRead.objects.select_related()
                .filter(privatetopic=self, user=user)
                .latest("privatepost__position_in_topic")
                .privatepost
            )

            next_post = PrivatePost.objects.filter(
                privatetopic__pk=self.pk, position_in_topic__gt=last_post.position_in_topic
            ).first()

            return next_post
        except (PrivatePost.DoesNotExist, PrivateTopicRead.DoesNotExist):
            return self.first_post()

    def resolve_last_read_post_absolute_url(self, user=None):
        """resolve the url that leads to the last post the current user has read.

        :return: the url
        :rtype: str
        """
        if user is None:
            user = get_current_user()

        try:
            pk, pos = self.resolve_last_post_pk_and_pos_read_by_user(user)
            page_nb = 1
            if pos > settings.ZDS_APP["forum"]["posts_per_page"]:
                page_nb += (pos - 1) // settings.ZDS_APP["forum"]["posts_per_page"]
            return f"{self.get_absolute_url()}?page={page_nb}#p{pk}"
        except PrivateTopicRead.DoesNotExist:
            return self.first_unread_post().get_absolute_url()

    def resolve_last_post_pk_and_pos_read_by_user(self, user):
        """Determine the primary ey of position of the last post read by a user.

        :param user: the current (authenticated) user. Please do not try with unauthenticated user, il would lead to a \
        useless request.
        :return: the primary key
        :rtype: int
        """
        t_read = (
            PrivateTopicRead.objects.select_related("privatepost")
            .filter(privatetopic__pk=self.pk, user__pk=user.pk)
            .latest("privatepost__position_in_topic")
        )
        if t_read:
            return t_read.privatepost.pk, t_read.privatepost.position_in_topic
        return list(
            PrivatePost.objects.filter(topic__pk=self.pk).order_by("position").values("pk", "position").first().values()
        )

    def one_participant_remaining(self):
        """
        Check if there is only one participant remaining in the private topic.

        :return: True if there is only one participant remaining, False otherwise.
        :rtype: bool
        """
        return self.participants.count() == 0

    def is_unread(self, user=None):
        """
        Check if a user has never read the current PrivateTopic.

        :param user: a user as Django User object. If None, the current user is used.
        :type user: User object
        :return: True if the PrivateTopic was never read
        :rtype: bool
        """
        # If user param is not defined, we get the current user
        if user is None:
            user = get_current_user()

        return is_privatetopic_unread(self, user)

    def is_author(self, user):
        """
        Check if a user is the author of the private topic.

        :param user: a given user.
        :return: True if the user is the author, False otherwise.
        """
        return self.author == user

    def set_as_author(self, user):
        """
        Set a participant as the author of the private topic.

        The previous author becomes a mere participant. If the user is already the author, nothing happens.

        :param user: a given user.
        :raise NotParticipatingError: if the user is not already participating in the private topic.
        """
        if not self.is_participant(user):
            raise NotParticipatingError
        if not self.is_author(user):  # nothing to do if user is already the author
            self.participants.add(self.author)
            self.participants.remove(user)
            self.author = user

    def is_participant(self, user):
        """
        Check if a given user is participating in the private topic.

        :param user: a given user.
        :return: True if the user is the author or a mere participant, False otherwise.
        """
        return self.is_author(user) or user in self.participants.all()

    def add_participant(self, user):
        """
        Add a participant to the private topic.
        If the user is already participating, do not add it again.
        Send the `participant_added` signal if successful.

        :param user: the user to add to the private topic
        :raise NotReachableError: if the user cannot receive private messages (e.g. a bot)
        """
        if not is_reachable(user):
            raise NotReachableError
        if not self.is_participant(user):  # avoid adding the same participant twice
            self.participants.add(user)
            signals.participant_added.send(sender=PrivateTopic, topic=self)

    def remove_participant(self, user):
        """
        Remove a participant from the private topic.
        If the removed participant is the author, set the first mere participant as the author.
        If the given user is not a participant, do nothing.
        Send the `participant_removed` signal if successful.

        :param user: the user to remove from the private topic.
        """
        if self.is_participant(user):
            if self.is_author(user):
                self.set_as_author(self.participants.first())
            self.participants.remove(user)
            signals.participant_removed.send(sender=PrivateTopic, topic=self)

    @staticmethod
    def has_read_permission(request):
        return request.user.is_authenticated

    def has_object_read_permission(self, request):
        return PrivateTopic.has_read_permission(request) and self.is_participant(request.user)

    @staticmethod
    def has_write_permission(request):
        return request.user.is_authenticated

    def has_object_write_permission(self, request):
        return PrivateTopic.has_write_permission(request) and self.is_participant(request.user)

    def has_object_update_permission(self, request):
        return PrivateTopic.has_write_permission(request) and self.is_author(request.user)


class PrivatePost(models.Model):
    """A private post written by a user."""

    class Meta:
        verbose_name = "Réponse à un message privé"
        verbose_name_plural = "Réponses à un message privé"

    privatetopic = models.ForeignKey(
        PrivateTopic, verbose_name="Message privé", db_index=True, on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, verbose_name="Auteur", related_name="privateposts", db_index=True, null=True, on_delete=models.SET_NULL
    )
    text = models.TextField("Texte")
    text_html = models.TextField("Texte en HTML")
    pubdate = models.DateTimeField("Date de publication", auto_now_add=True, db_index=True)
    update = models.DateTimeField("Date d'édition", null=True, blank=True)
    position_in_topic = models.IntegerField("Position dans le sujet", db_index=True)
    hat = models.ForeignKey(
        "utils.Hat",
        on_delete=models.SET_NULL,
        verbose_name="Casquette",
        related_name="privateposts",
        blank=True,
        null=True,
    )
    objects = PrivatePostManager()

    def __str__(self):
        """
        Human-readable representation of the PrivatePost model.

        :return: PrivatePost description
        :rtype: unicode
        """
        return f"<Post pour « {self.privatetopic} », #{self.pk}>"

    def get_absolute_url(self):
        """
        URL of a single PrivatePost object.

        :return: PrivatePost object URL
        :rtype: str
        """
        page = int(ceil(float(self.position_in_topic) / settings.ZDS_APP["forum"]["posts_per_page"]))

        return f"{self.privatetopic.get_absolute_url()}?page={page}#p{self.pk}"

    def is_author(self, user):
        """
        Check if the user given is the author of the message.

        :param user: Potential author of the message.
        :return: true if the user is the author.
        """
        return self.author == user

    def is_last_message(self, private_topic=None):
        """
        Check if the current message is the last one of its private topic.

        :param private_topic: Potential private topic of the message.
        :return: true if the current message is the last.
        """

        is_same_private_topic = self.privatetopic is not None
        if private_topic is not None:
            is_same_private_topic = private_topic == self.privatetopic
        return is_same_private_topic and self.privatetopic.last_message == self

    @staticmethod
    def has_read_permission(request):
        return request.user.is_authenticated

    def has_object_read_permission(self, request):
        return PrivateTopic.has_read_permission(request) and self.privatetopic.is_participant(request.user)

    @staticmethod
    def has_write_permission(request):
        return request.user.is_authenticated

    def has_object_write_permission(self, request):
        return PrivateTopic.has_write_permission(request) and self.privatetopic.is_participant(request.user)

    def has_object_update_permission(self, request):
        return PrivateTopic.has_write_permission(request) and self.is_last_message() and self.is_author(request.user)


class PrivateTopicRead(models.Model):
    """
    Small model which keeps track of the user viewing private topics.

    It remembers the topic he looked and what was the last private Post at this time.
    """

    class Meta:
        verbose_name = "Message privé lu"
        verbose_name_plural = "Messages privés lus"

    privatetopic = models.ForeignKey(PrivateTopic, db_index=True, on_delete=models.CASCADE)
    privatepost = models.ForeignKey(PrivatePost, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="privatetopics_read", db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        """
        Human-readable representation of the PrivateTopicRead model.

        :return: PrivateTopicRead description
        :rtype: unicode
        """
        return f"<Sujet « {self.privatetopic} » lu par {self.user}, #{self.privatepost.pk}>"


def is_privatetopic_unread(privatetopic, user=None):
    """
    Check if a private topic has been read by a user since it last post was added.

    :param privatetopic: a PrivateTopic to check
    :type privatetopic: PrivateTopic object
    :param user: a user as Django User object. If None, the current user is used
    :type user: User object
    :return: True if the PrivateTopic was never read
    :rtype: bool
    """
    # If user param is not defined, we get the current user
    if user is None:
        user = get_current_user()

    return (
        PrivateTopicRead.objects.filter(
            privatepost=privatetopic.last_message, privatetopic=privatetopic, user=user
        ).count()
        == 0
    )


def mark_read(privatetopic, user=None):
    """
    Mark a private topic as read for the user.

    :param privatetopic: a PrivateTopic to check
    :type privatetopic: PrivateTopic object
    :param user: a user as Django User object. If None, the current user is used
    :type user: User object
    :return: nothing is returned
    :rtype: None
    """
    # If user param is not defined, we get the current user
    if user is None:
        user = get_current_user()

    # Fetch the privateTopicRead concerning the given privateTopic and given (or current) user
    # Set the last read post as the current last post and save
    try:
        topic = PrivateTopicRead.objects.filter(privatetopic=privatetopic, user=user).get()
        topic.privatepost = privatetopic.last_message
    # Or create it if it does not exists yet
    except PrivateTopicRead.DoesNotExist:
        topic = PrivateTopicRead(privatepost=privatetopic.last_message, privatetopic=privatetopic, user=user)

    topic.save()
    signals.topic_read.send(sender=privatetopic.__class__, instance=privatetopic, user=user)
