from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import logging

from zds.mp.models import PrivateTopic, PrivatePost, mark_read
from zds.mp import signals
from zds.utils.templatetags.emarkdown import emarkdown

logger = logging.getLogger(__name__)


def send_mp(
    author,
    users,
    title,
    subtitle,
    text,
    send_by_mail=True,
    leave=True,
    direct=False,
    mark_as_read=False,
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
    :param send_by_mail:
    :param direct: send a mail directly without mp (ex : ban members who wont connect again)
    :param leave: if True, do not add the sender to the topic
    :param mark_as_read:
    :param hat: hat with which to send the private message
    :param automatically_read: a user or a list of users that will automatically be marked as having read of the mp
    :raise UnreachableUserError:
    """

    # Creating the thread
    limit = PrivateTopic._meta.get_field("title").max_length
    n_topic = PrivateTopic()
    n_topic.title = title[:limit]
    n_topic.subtitle = subtitle
    n_topic.pubdate = datetime.now()
    n_topic.author = author
    n_topic.save()

    # Add all participants on the MP.
    for participants in users:
        n_topic.participants.add(participants)

    topic = send_message_mp(author, n_topic, text, send_by_mail, direct, hat)
    if mark_as_read:
        mark_read(topic, author)
    if automatically_read:
        if not isinstance(automatically_read, list):
            automatically_read = [automatically_read]
        for not_notified_user in automatically_read:
            mark_read(n_topic, not_notified_user)
    if leave:
        topic.remove_participant(topic.author)
        topic.save()

    return topic


def send_message_mp(author, n_topic, text, send_by_mail=True, direct=False, hat=None, no_notification_for=None):
    """
    Send a post in an MP.

    :param author: sender of the private message
    :param n_topic: topic in which it will be sent
    :param text: content of the message
    :param send_by_mail: if True, also notify by email
    :param direct: send a mail directly without private message (ex : banned members who won't connect again)
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

    if not direct:
        signals.message_added.send(
            sender=post.__class__, instance=post, by_email=send_by_mail, no_notification_for=no_notification_for
        )

    if send_by_mail and direct:
        subject = "{} : {}".format(settings.ZDS_APP["site"]["literal_name"], n_topic.title)
        from_email = "{} <{}>".format(
            settings.ZDS_APP["site"]["literal_name"], settings.ZDS_APP["site"]["email_noreply"]
        )
        for recipient in n_topic.participants.values_list("email", flat=True):
            message_html = render_to_string("email/direct.html", {"msg": emarkdown(text)})
            message_txt = render_to_string("email/direct.txt", {"msg": text})

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [recipient])
            msg.attach_alternative(message_html, "text/html")
            try:
                msg.send()
            except Exception as e:
                logger.exception("Message was not sent to %s due to %s", recipient, e)
    if no_notification_for:
        if not isinstance(no_notification_for, list):
            no_notification_for = [no_notification_for]
        for not_notified_user in no_notification_for:
            mark_read(n_topic, not_notified_user)
    if author.pk not in [p.pk for p in n_topic.participants.all()] and author.pk != n_topic.author.pk:
        n_topic.participants.add(author)
        n_topic.save()

    return n_topic
