import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.core.validators import ValidationError, validate_email
from django.db import IntegrityError, models, transaction
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Post, Topic
from zds.notification.managers import (
    NewPublicationSubscriptionManager,
    NewTopicSubscriptionManager,
    NotificationManager,
    SubscriptionManager,
    TopicAnswerSubscriptionManager,
    TopicFollowedManager,
)
from zds.utils.misc import convert_camel_to_underscore

LOG = logging.getLogger(__name__)


class Subscription(models.Model):
    """
    Model used to register the subscription of a user to a set of notifications (regarding a tutorial, a forum, ...)
    """

    class Meta:
        verbose_name = _("Abonnement")
        verbose_name_plural = _("Abonnements")
        unique_together = (("user", "content_type", "object_id"),)

    user = models.ForeignKey(User, related_name="subscriber", db_index=True, on_delete=models.CASCADE)
    pubdate = models.DateTimeField(_("Date de création"), auto_now_add=True, db_index=True)
    is_active = models.BooleanField(_("Actif"), default=True, db_index=True)
    by_email = models.BooleanField(_("Recevoir un email"), default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    last_notification = models.ForeignKey(
        "Notification", related_name="last_notification", null=True, default=None, on_delete=models.SET_NULL
    )

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux notifications pour le {1}, #{2}>').format(
            self.user.username, self.content_type, self.object_id
        )

    def activate(self):
        """
        Activates the subscription if it's inactive. Does nothing otherwise
        """
        if not self.is_active:
            self.is_active = True
            self.save()

    def activate_email(self):
        """
        Activates the notifications by email (and the subscription itself if needed)
        """
        if not self.is_active or not self.by_email:
            self.is_active = True
            self.by_email = True
            self.save()

    def deactivate(self):
        """
        Deactivate the subscription if it is active. Does nothing otherwise
        """
        if self.is_active:
            self.is_active = False
            self.save()

    def deactivate_email(self):
        """
        Deactivate the email if it is active. Does nothing otherwise
        """
        if self.is_active and self.by_email:
            self.by_email = False
            self.save()

    def send_email(self, notification):
        """
        Sends an email notification
        """

        assert hasattr(self, "module")

        subject = _("{} - {} : {}").format(settings.ZDS_APP["site"]["literal_name"], self.module, notification.title)
        from_email = _("{} <{}>").format(
            settings.ZDS_APP["site"]["literal_name"], settings.ZDS_APP["site"]["email_noreply"]
        )

        receiver = self.user

        # This can happen when a user subscribes via social networks without providing an e-mail address
        try:
            validate_email(receiver.email)
        except ValidationError:
            return

        context = {
            "username": receiver.username,
            "title": notification.title,
            "url": settings.ZDS_APP["site"]["url"] + notification.url,
            "author": notification.sender.username,
            "site_name": settings.ZDS_APP["site"]["literal_name"],
        }
        message_html = render_to_string(
            "email/notification/" + convert_camel_to_underscore(self._meta.object_name) + ".html", context
        )
        message_txt = render_to_string(
            "email/notification/" + convert_camel_to_underscore(self._meta.object_name) + ".txt", context
        )

        msg = EmailMultiAlternatives(subject, message_txt, from_email, [receiver.email])
        msg.attach_alternative(message_html, "text/html")
        try:
            msg.send()
        except SMTPException:
            LOG.error("Failed sending mail for %s", self, exc_info=True)

    @staticmethod
    def has_read_permission(request):
        return request.user.is_authenticated

    def has_object_read_permission(self, request):
        return Subscription.has_read_permission(request) and self.user == request.user


class SingleNotificationMixin:
    """
    Mixin for the subscription that can only have one active notification at a time
    """

    def send_notification(self, content=None, send_email=True, sender=None):
        """
        Sends the notification about the given content
        :param content:  the content the notification is about
        :param sender: the user whose action triggered the notification
        :param send_email : whether an email must be sent if the subscription by email is active
        """
        assert hasattr(self, "last_notification")
        assert hasattr(self, "get_notification_url")
        assert hasattr(self, "get_notification_title")
        assert hasattr(self, "send_email")

        if self.last_notification is None or self.last_notification.is_read:
            notifications = list(Notification.objects.filter(subscription=self))
            if len(notifications) > 1:
                LOG.error("Found %s notifications for %s", len(notifications), self, exc_info=True)
                Notification.objects.filter(pk__in=[n.pk for n in notifications[1:]]).delete()
                LOG.info("Duplicates deleted.")

            notification = self.build_notification(content, sender)
            with transaction.atomic():
                notification.save()
                self.last_notification = notification
                self.save()

            if send_email and self.by_email:
                self.send_email(notification)
        elif self.last_notification is not None and not self.last_notification.is_read:
            # Update last notification if the new content is older (marking answer as unread)
            if self.last_notification.pubdate > content.pubdate:
                self.last_notification.content_object = content
                self.last_notification.save()

    def build_notification(self, content, sender):
        # If there isn't a notification yet or the last one is read, we generate a new one.
        try:
            notification = Notification.objects.get(subscription=self)
        except Notification.DoesNotExist:
            notification = Notification(subscription=self, content_object=content, sender=sender)
        notification.content_object = content
        notification.sender = sender
        notification.url = self.get_notification_url(content)
        notification.title = self.get_notification_title(content)
        notification.pubdate = content.pubdate
        notification.is_read = False
        return notification

    def mark_notification_read(self):
        """
        Marks the notification of the subscription as read.
        As there's only one active unread notification at all time,
        no need for more precision
        """
        if self.last_notification is not None:
            Notification.objects.filter(pk=self.last_notification.pk).update(is_read=True)


class MultipleNotificationsMixin:
    def send_notification(self, content=None, send_email=True, sender=None):
        """
        Sends the notification about the given content
        :param content:  the content the notification is about
        :param sender: the user whose action triggered the notification
        :param send_email : whether an email must be sent if the subscription by email is active
        """

        assert hasattr(self, "get_notification_url")
        assert hasattr(self, "get_notification_title")
        assert hasattr(self, "send_email")
        if self.last_notification and not self.last_notification.is_read:
            return

        notification = self.build_notification(content, sender)
        with transaction.atomic():
            notification.save()
            self.last_notification = notification
            self.save()

        if send_email and self.by_email:
            self.send_email(notification)

    def build_notification(self, content, sender):
        notification = Notification(subscription=self, content_object=content, sender=sender)
        notification.content_object = content
        notification.sender = sender
        notification.url = self.get_notification_url(content)
        notification.title = self.get_notification_title(content)
        notification.is_read = False
        return notification

    def mark_notification_read(self, content):
        """
        Marks the notification of the subscription as read.
        :param content : the content whose notification has been read
        """
        if content is None:
            raise ValueError("Object content of notification must be defined")

        try:
            with transaction.atomic():
                content_notification_type = ContentType.objects.get_for_model(content)
                notifications = list(
                    Notification.objects.filter(
                        subscription=self,
                        content_type__pk=content_notification_type.pk,
                        object_id=content.pk,
                        is_read=False,
                    )
                )
                # handles cases where a same subscription lead to several notifications
                if not notifications:
                    LOG.debug("nothing to mark as read")
                    return
                elif len(notifications) > 1:
                    content_type = getattr(content, "type", "forum")
                    content_title = getattr(content, "title", "message")
                    LOG.warning("%s notifications found for %s/%s", len(notifications), content_type, content_title)
                    for notif in notifications[1:]:
                        notif.delete()

                notification = notifications[0]
                notification.subscription = self
                notification.is_read = True

                notification.save()
        except IntegrityError:
            LOG.exception("Could not save %s", notification)


class AnswerSubscription(Subscription):
    """
    Subscription to new answer, either in a topic, a article or a tutorial
    NOT used directly, use one of its subtype
    """

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux réponses au {1} #{2}>').format(
            self.user.username, self.content_type, self.object_id
        )

    def get_notification_url(self, answer):
        return answer.get_absolute_url()

    def get_notification_title(self, answer):
        return self.content_object.title


class TopicAnswerSubscription(AnswerSubscription, SingleNotificationMixin):
    """
    Subscription to new answer in a topic
    """

    module = _("Forum")
    objects = TopicAnswerSubscriptionManager()

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux réponses au sujet #{1}>').format(self.user.username, self.object_id)


class PrivateTopicAnswerSubscription(AnswerSubscription, SingleNotificationMixin):
    """
    Subscription to new answer in a private topic.
    """

    module = _("Message privé")
    objects = SubscriptionManager()

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux réponses à la conversation privée #{1}>').format(
            self.user.username, self.object_id
        )


class ContentReactionAnswerSubscription(AnswerSubscription, SingleNotificationMixin):
    """
    Subscription to new answer in a publishable content.
    """

    module = _("Contenu")
    objects = SubscriptionManager()

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux réponses du contenu #{1}>').format(self.user.username, self.object_id)


class NewTopicSubscription(Subscription, MultipleNotificationsMixin):
    """
    Subscription to new topics in a forum or with a tag
    """

    module = _("Forum")
    objects = NewTopicSubscriptionManager()

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux nouveaux sujets du {1} #{2}>').format(
            self.user.username, self.content_type, self.object_id
        )

    def get_notification_url(self, topic):
        return topic.get_absolute_url()

    def get_notification_title(self, topic):
        return topic.title


class NewPublicationSubscription(Subscription, MultipleNotificationsMixin):
    """
    Subscription to new publications from a user.
    """

    module = _("Contenu")
    objects = NewPublicationSubscriptionManager()

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux nouvelles publications de l\'utilisateur #{1}>').format(
            self.user.username, self.object_id
        )

    def get_notification_url(self, content):
        return content.get_absolute_url_online()

    def get_notification_title(self, content):
        return content.title


class PingSubscription(AnswerSubscription, MultipleNotificationsMixin):
    """
    Subscription to ping of a user
    """

    module = _("Ping")
    objects = SubscriptionManager()

    def __str__(self):
        return _('<Abonnement du membre "{0}" aux mentions>').format(self.profile, self.object_id)

    @staticmethod
    def mark_inaccessible_ping_as_read_for_topic(topic):
        for post in Post.objects.filter(topic=topic):
            for notification in Notification.objects.filter(
                content_type__pk=ContentType.objects.get_for_model(post).pk, object_id=post.pk
            ):
                if not topic.forum.can_read(notification.subscription.user):
                    notification.is_read = True
                    notification.is_dead = True
                    notification.save(update_fields=["is_read"])

    def get_notification_title(self, answer):
        assert hasattr(answer, "author")
        assert hasattr(answer, "get_notification_title")

        return _("{0} vous a mentionné sur {1}.").format(answer.author, answer.get_notification_title())


class Notification(models.Model):
    """
    A notification
    """

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    subscription = models.ForeignKey(Subscription, related_name="subscription", db_index=True, on_delete=models.CASCADE)
    pubdate = models.DateTimeField(_("Date de création"), auto_now_add=True, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    is_read = models.BooleanField(_("Lue"), default=False, db_index=True)
    is_dead = models.BooleanField(_("Morte"), default=False)
    url = models.CharField("URL", max_length=255)
    sender = models.ForeignKey(User, related_name="sender", db_index=True, on_delete=models.CASCADE)
    title = models.CharField("Titre", max_length=200)
    objects = NotificationManager()

    def __str__(self):
        return _('Notification du membre "{0}" à propos de : {1} #{2} ({3})').format(
            self.subscription.user, self.content_type, self.content_object.pk, self.subscription
        )

    def __copy__(self):
        return Notification(
            subscription=self.subscription,
            pubdate=self.pubdate,
            content_type=self.content_type,
            object_id=self.object_id,
            content_object=self.content_object,
            is_read=self.is_read,
            is_dead=self.is_dead,
            url=self.url,
            sender=self.sender,
            title=self.title,
        )

    @staticmethod
    def has_read_permission(request):
        return request.user.is_authenticated

    def has_object_read_permission(self, request):
        return Notification.has_read_permission(request) and self.subscription.user == request.user


class TopicFollowed(models.Model):
    """
    This model tracks which user follows which topic.
    It serves only to manual topic following.
    This model also indicates if the topic is followed by email.
    """

    class Meta:
        verbose_name = "Sujet suivi"
        verbose_name_plural = "Sujets suivis"

    topic = models.ForeignKey(Topic, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="topics_followed", db_index=True, on_delete=models.CASCADE)
    email = models.BooleanField("Notification par courriel", default=False, db_index=True)
    objects = TopicFollowedManager()

    def __str__(self):
        return f'<Sujet "{self.topic.title}" suivi par {self.user.username}>'
