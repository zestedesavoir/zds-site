import logging
from contextlib import suppress
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from zds.mp import signals
from zds.mp.models import NotReachableError, PrivatePost, PrivateTopic, mark_read
from zds.utils.templatetags.emarkdown import emarkdown

logger = logging.getLogger(__name__)


def send_mp(
    author,
    users,
    title,
    subtitle,
    text,
    send_by_mail=True,
    force_email=False,
    leave=True,
    hat=None,
    automatically_read=None,
):
    """
    Send a private message in a new private topic.

    :param author: sender of the message and author of the private topic
    :param users: list of users receiving the message (participants of the private topic)
    :param title: title of the private topic
    :param subtitle: subtitle of the private topic
    :param text: content of the private message
    :param send_by_mail: if True, also notify by email
    :param force_email: if True, send email even if the user has not enabled email notifications
    :param leave: if True, do not add the sender to the topic
    :param hat: hat with which to send the private message
    :param automatically_read: a user or a list of users that will automatically be marked as having read of the mp
    :raise UnreachableUserError:
    """

    n_topic = PrivateTopic.create(title=title, subtitle=subtitle, author=author, recipients=users)
    signals.topic_created.send(sender=PrivateTopic, topic=n_topic, by_email=send_by_mail)

    topic = send_message_mp(author, n_topic, text, send_by_mail, force_email, hat)

    if automatically_read:
        if not isinstance(automatically_read, list):
            automatically_read = [automatically_read]
        for not_notified_user in automatically_read:
            mark_read(n_topic, not_notified_user)
    if leave:
        topic.remove_participant(topic.author)
        topic.save()

    return topic


def send_message_mp(author, n_topic, text, send_by_mail=True, force_email=False, hat=None, no_notification_for=None):
    """
    Send a post in an MP.

    :param author: sender of the private message
    :param n_topic: topic in which it will be sent
    :param text: content of the message
    :param send_by_mail: if True, also notify by email
    :param force_email: if True, send email even if the user has not enabled email notifications
    :param hat: hat attached to the message
    :param no_notification_for: list of participants who won't be notified of the message
    """

    # Getting the position of the post
    if n_topic.last_message is None:
        pos = 1
    else:
        pos = n_topic.last_message.position_in_topic + 1

    # Add the first message
    post = PrivatePost()
    post.privatetopic = n_topic
    post.author = author
    post.text = text
    post.text_html = emarkdown(text)
    post.pubdate = datetime.now()
    post.position_in_topic = pos
    post.hat = hat
    post.save()

    n_topic.last_message = post
    n_topic.save()

    signals.message_added.send(
        sender=post.__class__,
        post=post,
        by_email=send_by_mail,
        force_email=force_email,
        no_notification_for=no_notification_for,
    )
    if no_notification_for:
        if not isinstance(no_notification_for, list):
            no_notification_for = [no_notification_for]
        for not_notified_user in no_notification_for:
            mark_read(n_topic, not_notified_user)

    # There's no need to inform of the new participant
    # because participants are already notified through the `message_added` signal.
    # If we tried to add the bot, that's fine (a better solution would be welcome though)
    with suppress(NotReachableError):
        n_topic.add_participant(author, silent=True)
        n_topic.save()

    return n_topic
