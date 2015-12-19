# -*- coding: utf-8 -*-s
from smtplib import SMTPException

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from zds import settings
from zds.forum.models import Topic
from zds.member.models import Profile
from zds.notification.managers import TopicFollowedManager, NotificationManager
from zds.utils import get_current_user
from zds.utils.misc import convert_camel_to_underscore


class Subscription(models.Model):
    """
    Model used to register the subscription of a user to a set of notifications (regarding a tutorial, a forum, ...)
    """

    class Meta:
        verbose_name = _(u'Abonnement')
        verbose_name_plural = _(u'Abonnements')

    profile = models.ForeignKey(Profile, related_name='subscriber', db_index=True)
    pubdate = models.DateTimeField(_(u'Date de création'), auto_now_add=True, db_index=True)
    is_active = models.BooleanField(_(u'Actif'), default=True, db_index=True)
    by_email = models.BooleanField(_(u'Recevoir un email'), default=False)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    last_notification = models.ForeignKey(u'Notification', related_name="last_notification", null=True, default=None)

    def __unicode__(self):
        return _(u'<Abonnement du membre "{0}" aux notifications pour le {1}, #{2}>')\
            .format(self.profile, self.content_type, self.object_id)

    def activate(self):
        """
        Activates the subscription if it's inactive. Does nothing otherwise
        """
        if not self.is_active:
            self.is_active = True
            self.save()

    def activate_email(self):
        """
        Acitvates the notifications by email (and the subscription itself if needed)
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

    def set_last_notification(self, notification):
        """
        Replace last_notification by the one given
        """
        self.last_notification = notification
        self.save()

    def send_email(self, notification):
        """
        Sends an email notification
        """

        assert hasattr(self, "module")

        subject = _(u"{} - {} : {}").format(settings.ZDS_APP['site']['litteral_name'], self.module, notification.title)
        from_email = _(u"{} <{}>").format(settings.ZDS_APP['site']['litteral_name'],
                                          settings.ZDS_APP['site']['email_noreply'])

        receiver = self.profile.user
        context = {
            'username': self.profile.user.username,
            'title': notification.title,
            'url': settings.ZDS_APP['site']['url'] + notification.url,
            'author': notification.sender.user.username,
            'site_name': settings.ZDS_APP['site']['litteral_name']
        }
        message_html = render_to_string(
            'email/notification/' + convert_camel_to_underscore(self._meta.object_name) + '.html', context)
        message_txt = render_to_string(
            'email/notification/' + convert_camel_to_underscore(self._meta.object_name) + '.txt', context)

        msg = EmailMultiAlternatives(subject, message_txt, from_email, [receiver.email])
        msg.attach_alternative(message_html, "text/html")
        try:
            msg.send()
        except SMTPException:
            pass


class SingleNotificationMixin(object):
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
        assert hasattr(self, "get_notification_url")
        assert hasattr(self, "get_notification_title")
        assert hasattr(self, "send_email")

        # If the last notification has not been read yet, no new notification is sent
        if self.last_notification is None or self.last_notification.is_read:
            notification = Notification(subscription=self, content_object=content, sender=sender)
            notification.url = self.get_notification_url(content)
            notification.title = self.get_notification_title(content)
            notification.save()
            self.set_last_notification(notification)
            self.save()

            if send_email and self.by_email:
                self.send_email(notification)
        elif self.last_notification is not None:
            # Update last notif if the new content is older (case of unreading answer)
            if not self.last_notification.is_read and self.last_notification.pubdate > content.pubdate:
                self.last_notification.content_object = content
                self.last_notification.save()

    def mark_notification_read(self):
        """
        Marks the notification of the subscription as read.
        As there's only one active unread notification at all time,
        no need for more precision
        """
        if self.last_notification is not None:
            self.last_notification.is_read = True
            self.last_notification.save()


class MultipleNotificationsMixin(object):

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

        notification = Notification(subscription=self, content_object=content, sender=sender)
        notification.url = self.get_notification_url(content)
        notification.title = self.get_notification_title(content)
        notification.save()
        self.set_last_notification(notification)

        if send_email and self.by_email:
            self.send_email(notification)

    def mark_notification_read(self, content):
        """
        Marks the notification of the subscription as read.
        :param content : the content whose notification has been read
        """
        if content is None:
            raise Exception('Object content of notification must be defined')

        content_notification_type = ContentType.objects.get_for_model(content)
        try:
            notification = Notification.objects.get(subscription=self,
                                                    content_type__pk=content_notification_type.pk,
                                                    object_id=content.pk, is_read=False)
            if notification is not None:
                notification.is_read = True
                notification.save()
        except Notification.DoesNotExist:
            pass


class AnswerSubscription(Subscription):
    """
    Subscription to new answer, either in a topic, a article or a tutorial
    NOT used directly, use one of its subtype
    """
    def __unicode__(self):
        return _(u'<Abonnement du membre "{0}" aux réponses au {1} #{2}>')\
            .format(self.profile, self.content_type, self.object_id)

    def get_notification_url(self, answer):
        return answer.get_absolute_url()

    def get_notification_title(self, answer):
        return self.content_object.title


class Notification(models.Model):
    """
    A notification
    """
    class Meta:
        verbose_name = _(u'Notification')
        verbose_name_plural = _(u'Notifications')

    subscription = models.ForeignKey(Subscription, related_name='subscription', db_index=True)
    pubdate = models.DateTimeField(_(u'Date de création'), auto_now_add=True, db_index=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    is_read = models.BooleanField(_(u'Lue'), default=False, db_index=True)
    url = models.CharField('URL', max_length=255)
    sender = models.ForeignKey(Profile, related_name='sender', db_index=True)
    title = models.CharField('Titre', max_length=200)
    objects = NotificationManager()

    def __unicode__(self):
        return _(u'Notification du membre "{0}" à propos de : {1} #{2} ({3})')\
            .format(self.subscription.profile, self.content_type, self.content_object.pk, self.subscription)


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
