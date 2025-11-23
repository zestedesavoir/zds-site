import logging
import os
import string
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

from zds.member.utils import get_bot_account
from zds.mp.models import PrivateTopic
from zds.mp.utils import send_mp
from zds.tutorialv2.models import TYPE_CHOICES, TYPE_CHOICES_DICT
from zds.utils import old_slugify, signals
from zds.utils.misc import contains_utf8mb4
from zds.utils.templatetags.emarkdown import render_markdown
from zds.utils.uuslug_wrapper import uuslug

logger = logging.getLogger(__name__)


def image_path_category(instance, filename):
    """Return path to an image."""
    ext = filename.split(".")[-1]
    filename = f"{str(uuid.uuid4())}.{string.lower(ext)}"
    return os.path.join("categorie/normal", str(instance.pk), filename)


def image_path_help(instance, filename):
    """Return path to an image."""
    ext = filename.split(".")[-1]
    filename = f"{str(uuid.uuid4())}.{string.lower(ext)}"
    return os.path.join("helps/normal", str(instance.pk), filename)


class Category(models.Model):
    """Common category for several concepts of the application."""

    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categories"

    title = models.CharField("Titre", unique=True, max_length=80)
    description = models.TextField("Description")
    position = models.IntegerField("Position", default=0, db_index=True)

    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.title

    def get_subcategories(self):
        return [
            a.subcategory
            for a in CategorySubCategory.objects.filter(is_main=True, category__pk=self.pk)
            .prefetch_related("subcategory")
            .all()
        ]


class SubCategory(models.Model):
    """Common subcategory for several concepts of the application."""

    class Meta:
        verbose_name = "Sous-categorie"
        verbose_name_plural = "Sous-categories"

    title = models.CharField("Titre", max_length=80, unique=True)
    subtitle = models.CharField("Sous-titre", max_length=200)
    position = models.IntegerField("Position", db_index=True, default=0)

    image = models.ImageField(upload_to=image_path_category, blank=True, null=True)

    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url_tutorial(self):
        url = reverse("tutorial-index")
        url += f"?tag={self.slug}"
        return url

    def get_absolute_url_article(self):
        url = reverse("article-index")
        url += f"?tag={self.slug}"
        return url

    def get_parent_category(self):
        """
        Get the parent of the category.

        :return: the parent category.
        :rtype: Category
        """
        try:
            return CategorySubCategory.objects.filter(subcategory=self).last().category
        except AttributeError:  # no CategorySubCategory
            return None


class CategorySubCategory(models.Model):
    """ManyToMany between Category and SubCategory but save a boolean to know
    if category is his main category."""

    class Meta:
        verbose_name = "Hierarchie catégorie"
        verbose_name_plural = "Hierarchies catégories"

    category = models.ForeignKey(Category, verbose_name="Catégorie", db_index=True, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, verbose_name="Sous-Catégorie", db_index=True, on_delete=models.CASCADE)
    is_main = models.BooleanField("Est la catégorie principale", default=True, db_index=True)

    def __str__(self):
        """Textual Link Form."""
        if self.is_main:
            return f"[{self.category.title}][main]: {self.subcategory.title}"
        else:
            return f"[{self.category.title}]: {self.subcategory.title}"


class Licence(models.Model):
    """Publication licence."""

    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"

    code = models.CharField("Code", max_length=20)
    title = models.CharField("Titre", max_length=80)
    description = models.TextField("Description")

    def __str__(self):
        """Textual Licence Form."""
        return self.title


class Hat(models.Model):
    """
    Hats are labels that users can add to their messages.
    Each member can be allowed to use several hats.
    A hat may also be linked to a group, which
    allows all members of the group to use it.
    It can be used for exemple to allow members to identify
    that a moderation message was posted by a staff member.
    """

    name = models.CharField("Casquette", max_length=40, unique=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        verbose_name="Groupe possédant la casquette",
        related_name="hats",
        db_index=True,
        null=True,
        blank=True,
    )
    is_staff = models.BooleanField("Casquette interne au site", default=False)

    class Meta:
        verbose_name = "Casquette"
        verbose_name_plural = "Casquettes"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("hat-detail", args=[self.pk])

    def get_users(self):
        """
        Return all users being allowed to use this hat.
        """
        if self.group:
            return self.group.user_set.all()
        else:
            return [p.user for p in self.profile_set.all()]

    def get_users_count(self):
        return len(self.get_users())

    def get_users_preview(self):
        return self.get_users()[: settings.ZDS_APP["member"]["users_in_hats_list"]]


class HatRequest(models.Model):
    """
    A hat requested by a user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur", related_name="requested_hats")
    hat = models.CharField("Casquette", max_length=40)
    reason = models.TextField("Raison de la demande", max_length=3000)
    date = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Date de la demande", db_column="request_date"
    )
    is_granted = models.BooleanField("Est acceptée", null=True)
    solved_at = models.DateTimeField("Date de résolution", blank=True, null=True)
    moderator = models.ForeignKey(User, verbose_name="Modérateur", blank=True, null=True, on_delete=models.SET_NULL)
    comment = models.TextField("Commentaire", max_length=1000, blank=True)

    class Meta:
        verbose_name = "Demande de casquette"
        verbose_name_plural = "Demandes de casquettes"

    def __str__(self):
        return f"Hat {self.hat} requested by {self.user.username}"

    def get_absolute_url(self):
        return reverse("hat-request", args=[self.pk])

    def get_hat(self, create=False):
        """
        Get hat that matches this request. If it doesn't exist, it is created
        or `None` is returned according to the `create` parameter.
        """

        try:
            return Hat.objects.get(name__iexact=self.hat)
        except Hat.DoesNotExist:
            if create:
                return Hat.objects.create(name=self.hat)
            else:
                return None

    def solve(self, is_granted, moderator=None, comment="", hat_name=None):
        """
        Solve a hat request by granting or denying the requested hat according
        to the `is_granted` parameter.
        """

        if self.is_granted is not None:
            raise Exception("This request is already solved.")

        if moderator is None:
            moderator = get_bot_account()

        if is_granted:
            if self.get_hat() is None and hat_name:
                self.hat = get_hat_to_add(hat_name, self.user).name
            self.user.profile.hats.add(self.get_hat(create=True))
        self.is_granted = is_granted
        self.moderator = moderator
        self.comment = comment[:1000]
        self.solved_at = datetime.now()
        self.save()
        self.notify_member()

    def notify_member(self):
        """
        Notify the request author about the decision that has been made.
        """

        if self.is_granted is None:
            raise Exception("The request must have been solved to use this method.")

        solved_by_bot = self.moderator == get_bot_account()

        message = render_to_string(
            "member/messages/hat_request_decision.md",
            {
                "is_granted": self.is_granted,
                "hat": self.hat,
                "comment": self.comment,
                "solved_by_bot": solved_by_bot,
            },
        )
        send_mp(
            self.moderator,
            [self.user],
            _("Casquette « {} »").format(self.hat),
            "",
            message,
            leave=solved_by_bot,
            hat=get_hat_from_settings("hats_management"),
        )


@receiver(models.signals.post_save, sender=Hat)
def prevent_users_getting_hat_linked_to_group(sender, instance, **kwargs):
    """
    When a hat is saved with a linked group, all users that have gotten it by another way
    lose it to prevent a hat from being linked to a user through their profile and one of their groups.
    Hat requests for this hat are also canceled.
    """
    if instance.group:
        instance.profile_set.clear()
        for request in HatRequest.objects.filter(hat__iexact=instance.name, is_granted__isnull=True):
            request.solve(
                is_granted=False,
                comment=_(
                    "La demande a été automatiquement annulée car la casquette est désormais accordée "
                    "aux membres d’un groupe particulier. Vous l’avez reçue si "
                    "vous en êtes membre."
                ),
            )


def get_hat_from_request(request, author=None):
    """
    Return a hat that will be used for a post.
    This checks that the user is allowed to use this hat.
    """

    if author is None:
        author = request.user
    if not request.POST.get("with_hat", None):
        return None
    try:
        hat = Hat.objects.get(pk=int(request.POST.get("with_hat")))
        if hat not in author.profile.get_hats():
            raise ValueError
        return hat
    except (ValueError, Hat.DoesNotExist):
        logger.warning("User #{} failed to use hat #{}.".format(request.user.pk, request.POST.get("hat")))
        return None


def get_hat_from_settings(key):
    hat_name = settings.ZDS_APP["hats"][key]
    hat, _ = Hat.objects.get_or_create(name__iexact=hat_name, defaults={"name": hat_name})
    return hat


def get_hat_to_add(hat_name, user):
    """
    Return a hat that will be added to a user.
    This function creates the hat if it does not exist,
    so be sure you will need it!
    """

    hat_name = hat_name.strip()
    if not hat_name:
        raise ValueError(_("Veuillez saisir une casquette."))
    if contains_utf8mb4(hat_name):
        raise ValueError(
            _("La casquette saisie contient des caractères utf8mb4, " "ceux-ci ne peuvent pas être utilisés.")
        )
    if len(hat_name) > 40:
        raise ValueError(_("La longueur des casquettes est limitée à 40 caractères."))
    hat, created = Hat.objects.get_or_create(name__iexact=hat_name, defaults={"name": hat_name})
    if created:
        logger.info(f'Hat #{hat.pk} "{hat.name}" has been created.')
    if hat in user.profile.get_hats():
        raise ValueError(_(f"{user.username} possède déjà la casquette « {hat.name} »."))
    if hat.group:
        raise ValueError(
            _(
                "La casquette « {} » est accordée automatiquement aux membres d'un groupe particulier "
                "et ne peut donc pas être ajoutée à un membre externe à ce groupe.".format(hat.name)
            )
        )
    return hat


class Comment(models.Model):
    """Comment in forum, articles, tutorial, chapter, etc."""

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

        permissions = [("change_comment_potential_spam", "Can change the potential spam status of a comment")]

    objects = InheritanceManager()

    author = models.ForeignKey(
        User,
        verbose_name="Auteur",
        related_name="comments",
        db_index=True,
        # better on_delete with "set anonymous?"
        on_delete=models.CASCADE,
    )
    editor = models.ForeignKey(
        User, verbose_name="Editeur", related_name="comments-editor+", null=True, blank=True, on_delete=models.SET_NULL
    )
    ip_address = models.CharField("Adresse IP de l'auteur ", max_length=39)

    position = models.IntegerField("Position", db_index=True)

    text = models.TextField("Texte")
    text_html = models.TextField("Texte en Html")

    like = models.IntegerField("Likes", default=0)
    dislike = models.IntegerField("Dislikes", default=0)

    pubdate = models.DateTimeField("Date de publication", auto_now_add=True, db_index=True)
    update = models.DateTimeField("Date d'édition", null=True, blank=True)

    is_visible = models.BooleanField("Est visible", default=True)
    text_hidden = models.CharField("Texte de masquage ", max_length=80, default="")

    hat = models.ForeignKey(
        Hat, verbose_name="Casquette", on_delete=models.SET_NULL, related_name="comments", blank=True, null=True
    )

    is_potential_spam = models.BooleanField("Est potentiellement du spam", default=False)

    def update_content(self, text, on_error=None):
        """
        Updates the content of this comment.

        This method will render the new comment to HTML, store the rendered
        version, and store data to later analyze pings and spam.

        This method updates fields, but does not save the instance.

        :param text: The new comment content.
        :param on_error: A callable called if zmd returns an error, provided
                         with a single argument: a list of user-friendly errors.
                         See render_markdown.
        """
        # This attribute will be used by `_save_check_spam`, called after save (but not saved into the database).
        # We only update it if it does not already exist, so if this method is called multiple times, the oldest
        # version (i.e. the one currently in the database) is used for comparison. `_save_check_spam` will delete
        # the attribute, so if we re-save the same instance, this will be re-set.
        if not hasattr(self, "old_text"):
            self.old_text = self.text

        _, old_metadata, _ = render_markdown(self.text)
        html, new_metadata, _ = render_markdown(text, on_error=on_error)

        # These attributes will be used by `_save_compute_pings` to create notifications if needed.
        # For the same reason as `old_text`, we only update `old_metadata` if not already set.
        if not hasattr(self, "old_metadata"):
            self.old_metadata = old_metadata
        self.new_metadata = new_metadata

        self.text = text
        self.text_html = html

    def save(self, *args, **kwargs):
        """
        We override the save method for two tasks:
        1. we want to analyze the pings in the message to know if notifications
        needs to be created;
        2. if this comment is marked as potential spam, we need to open an alert
        in case of update by its author.
        """
        super().save(*args, **kwargs)

        self._save_compute_pings()
        self._save_check_spam()

    def _save_compute_pings(self):
        """
        This method, called on the save method when the save is complete,
        analyzes pings to create, or delete, ping notifications. It must run
        when the instance is saved (for new messages) as notifications
        references messages in the database.
        """

        # If `update_content` was not called, there is nothing to do as the
        # message's content stayed the same.
        if not hasattr(self, "old_metadata") or not hasattr(self, "new_metadata"):
            return

        def filter_usernames(original_list):
            # removes duplicates and the message's author
            filtered_list = []
            for username in original_list:
                if username != self.author.username and username not in filtered_list:
                    filtered_list.append(username)
            return filtered_list

        max_pings_allowed = settings.ZDS_APP["comment"]["max_pings"]
        pinged_usernames_from_new_text = filter_usernames(self.new_metadata.get("ping", []))[:max_pings_allowed]
        pinged_usernames_from_old_text = filter_usernames(self.old_metadata.get("ping", []))[:max_pings_allowed]

        pinged_usernames = set(pinged_usernames_from_new_text) - set(pinged_usernames_from_old_text)
        pinged_users = User.objects.filter(username__in=pinged_usernames)
        for pinged_user in pinged_users:
            signals.ping.send(sender=self.__class__, instance=self, user=pinged_user)

        unpinged_usernames = set(pinged_usernames_from_old_text) - set(pinged_usernames_from_new_text)
        unpinged_users = User.objects.filter(username__in=unpinged_usernames)
        for unpinged_user in unpinged_users:
            signals.unping.send(self.author, instance=self, user=unpinged_user)

        del self.old_metadata
        del self.new_metadata

    def _save_check_spam(self):
        """
        This method checks if this message is marked as spam and if it was
        modified by its author. If so, an alert is created.
        """
        # For new comments (if there is no editor), this does not apply.
        # If we edit a comment but the `old_text` attribute is not set, this means
        # `Comment.update_content` was not called: the content was not updated.
        if not hasattr(self, "old_text") or not self.editor:
            return

        # If this post is marked as potential spam, we open an alert to notify the staff that
        # the post was edited. If an open alert already exists for this reason, we update the
        # date of this alert to avoid lots of them stacking up.
        if self.old_text != self.text and self.is_potential_spam and self.editor == self.author:
            bot = get_bot_account()
            alert_text = _("Ce message, soupçonné d'être un spam, a été modifié.")

            try:
                alert = self.alerts_on_this_comment.filter(author=bot, text=alert_text, solved=False).latest()
                alert.pubdate = datetime.now()
                alert.save()
            except Alert.DoesNotExist:
                # We first have to compute the correct scope
                if type(self).__name__ == "ContentReaction":
                    scope = self.related_content.type
                else:
                    scope = "FORUM"

                Alert(author=bot, comment=self, scope=scope, text=alert_text, pubdate=datetime.now()).save()

        del self.old_text

    def hide_comment_by_user(self, user, text_hidden):
        """Hide a comment and save it

        :param user: the user that hid the comment
        :param text_hidden: the hide reason
        :return:
        """
        self.is_visible = False
        self.text_hidden = text_hidden
        self.editor = user
        self.save()

    def get_user_vote(self, user):
        """Get a user vote (like, dislike or neutral)"""
        if user.is_authenticated:
            try:
                user_vote = "like" if CommentVote.objects.get(user=user, comment=self).positive else "dislike"
            except CommentVote.DoesNotExist:
                user_vote = "neutral"
        else:
            user_vote = "neutral"

        return user_vote

    def set_user_vote(self, user, vote):
        """Set a user vote (like, dislike or neutral)"""
        if vote == "neutral":
            CommentVote.objects.filter(user=user, comment=self).delete()
        else:
            CommentVote.objects.update_or_create(user=user, comment=self, defaults={"positive": (vote == "like")})

        self.like = CommentVote.objects.filter(positive=True, comment=self).count()
        self.dislike = CommentVote.objects.filter(positive=False, comment=self).count()

    def get_votes(self, type=None):
        """Get the non-anonymous votes"""
        if not hasattr(self, "votes"):
            self.votes = (
                CommentVote.objects.filter(comment=self, id__gt=settings.VOTES_ID_LIMIT).select_related("user").all()
            )

        return self.votes

    def get_likers(self):
        """Get the list of the users that liked this Comment"""
        return [vote.user for vote in self.get_votes() if vote.positive]

    def get_dislikers(self):
        """Get the list of the users that disliked this Comment"""
        return [vote.user for vote in self.get_votes() if not vote.positive]

    def get_absolute_url(self):
        return Comment.objects.get_subclass(id=self.id).get_absolute_url()

    def __str__(self):
        return f"Comment by {self.author.username}"


class CommentEdit(models.Model):
    """Archive for editing a comment."""

    class Meta:
        verbose_name = "Édition d'un message"
        verbose_name_plural = "Éditions de messages"

    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, verbose_name="Message", related_name="edits", db_index=True
    )
    editor = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Éditeur", related_name="edits", db_index=True
    )
    date = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Date de l'édition", db_column="edit_date"
    )
    original_text = models.TextField("Contenu d'origine", blank=True)
    deleted_at = models.DateTimeField(db_index=True, verbose_name="Date de suppression", blank=True, null=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Supprimé par",
        related_name="deleted_edits",
        db_index=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Edit by {self.editor.username} on a comment of {self.comment.author.username}"


class Alert(models.Model):
    """Alerts on Profiles, PublishedContents and all kinds of Comments.

    The scope field indicates on which type of element the alert is made:
    - PROFILE: the profile of a member
    - FORUM: a post on a topic in a forum
    - CONTENT: the content (article, opinion or tutorial) itself
    - elements of TYPE_CHOICES (ARTICLE, OPINION, TUTORIAL): a comment on a content of this type
    """

    SCOPE_CHOICES = [
        ("PROFILE", _("Profil")),
        ("FORUM", _("Forum")),
        ("CONTENT", _("Contenu")),
    ] + TYPE_CHOICES

    SCOPE_CHOICES_DICT = dict(SCOPE_CHOICES)

    author = models.ForeignKey(
        User, verbose_name="Auteur", related_name="alerts", db_index=True, on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment,
        verbose_name="Commentaire",
        related_name="alerts_on_this_comment",
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    # use of string definition of pk to avoid circular import.
    profile = models.ForeignKey(
        "member.Profile",
        verbose_name="Profil",
        related_name="alerts_on_this_profile",
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    content = models.ForeignKey(
        "tutorialv2.PublishableContent",
        verbose_name="Contenu",
        related_name="alerts_on_this_content",
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, db_index=True)
    text = models.TextField("Texte d'alerte")
    pubdate = models.DateTimeField("Date de création", db_index=True)
    solved = models.BooleanField("Est résolue", default=False)
    moderator = models.ForeignKey(
        User,
        verbose_name="Modérateur",
        related_name="solved_alerts",
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # sent to the alert creator
    resolve_reason = models.TextField("Texte de résolution", null=True, blank=True)
    # PrivateTopic sending the resolve_reason to the alert creator
    privatetopic = models.ForeignKey(
        PrivateTopic, on_delete=models.SET_NULL, verbose_name="Message privé", db_index=True, null=True, blank=True
    )
    solved_date = models.DateTimeField("Date de résolution", db_index=True, null=True, blank=True)

    def get_type(self):
        if self.scope in TYPE_CHOICES_DICT:
            assert self.comment is not None
            if self.is_on_comment_on_unpublished_content():
                return _(f"Commentaire sur un {self.SCOPE_CHOICES_DICT[self.scope].lower()} dépublié")
            else:
                return _(f"Commentaire sur un {self.SCOPE_CHOICES_DICT[self.scope].lower()}")
        elif self.scope == "FORUM":
            assert self.comment is not None
            return _("Message de forum")
        elif self.scope == "PROFILE":
            assert self.profile is not None
            return _("Profil")
        else:
            assert self.content is not None
            return self.SCOPE_CHOICES_DICT[self.content.type]

    def is_on_comment_on_unpublished_content(self):
        return self.scope in TYPE_CHOICES_DICT and not self.get_comment_subclass().related_content.in_public()

    def is_automated(self):
        """Returns true if this alert was opened automatically."""
        return self.author.username == settings.ZDS_APP["member"]["bot_account"]

    def solve(self, moderator, resolve_reason="", msg_title="", msg_content=""):
        """Solve the alert and send a private message to the author if a reason is given

        :param resolve_reason: reason
        :type resolve_reason: str
        """
        self.resolve_reason = resolve_reason or None
        if msg_title and msg_content:
            bot = get_bot_account()
            privatetopic = send_mp(
                bot,
                [self.author],
                msg_title,
                "",
                msg_content,
                send_by_mail=True,
                hat=get_hat_from_settings("moderation"),
            )
            self.privatetopic = privatetopic

        self.solved = True
        self.moderator = moderator
        self.solved_date = datetime.now()
        self.save()

    def get_comment(self):
        return Comment.objects.get(id=self.comment.id)

    def get_comment_subclass(self):
        """Used to retrieve comment URLs (simple call to get_absolute_url
        doesn't work: objects are retrived as Comment and not subclasses) As
        real Comment implementation (subclasses) can't be hard-coded due to
        unresolvable import loops, use InheritanceManager from django-model-
        utils."""
        return Comment.objects.get_subclass(id=self.comment.id)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        get_latest_by = "pubdate"


class CommentVote(models.Model):
    """Set of comment votes."""

    class Meta:
        verbose_name = "Vote"
        verbose_name_plural = "Votes"
        unique_together = ("user", "comment")

    comment = models.ForeignKey(Comment, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    positive = models.BooleanField("Est un vote positif", default=True)

    def __str__(self):
        return f"Vote from {self.user.username} about Comment#{self.comment.pk} thumb_up={self.positive}"


class Tag(models.Model):
    """Set of tags."""

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    title = models.CharField("Titre", max_length=30, unique=True, db_index=True)
    slug = models.SlugField("Slug", max_length=30, unique=True)

    def __str__(self):
        """Textual Link Form."""
        return self.title

    def get_absolute_url(self):
        return reverse("forum:topic-tag-find", kwargs={"tag_slug": self.slug})

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        if not self.title or not old_slugify(self.title.replace("-", "")):
            raise ValueError(f'Tag "{self.title}" is not correct')
        self.title = smart_str(self.title).lower()
        self.slug = uuslug(self.title, instance=self, max_length=Tag._meta.get_field("slug").max_length)
        super().save(*args, **kwargs)

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True
