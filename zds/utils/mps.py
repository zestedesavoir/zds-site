from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from zds.mp.models import PrivateTopic, PrivatePost
from zds.notification import signals
from zds.utils.templatetags.emarkdown import emarkdown


def send_mp(
        author,
        users,
        title,
        subtitle,
        text,
        send_by_mail=True,
        leave=True,
        direct=False):
    """
    Send MP at members.
    Most of the param are obvious, excepted :
    * direct : send a mail directly without mp (ex : ban members who wont connect again)
    * leave : the author leave the conversation (usefull for the bot : it wont read the response a member could send)
    """

    # Creating the thread
    limit = PrivateTopic._meta.get_field('title').max_length
    n_topic = PrivateTopic()
    n_topic.title = title[:limit]
    n_topic.subtitle = subtitle
    n_topic.pubdate = datetime.now()
    n_topic.author = author
    n_topic.save()

    # Add all participants on the MP.
    for part in users:
        n_topic.participants.add(part)

    topic = send_message_mp(author, n_topic, text, send_by_mail, direct)

    if leave:
        move = topic.participants.first()
        topic.author = move
        topic.participants.remove(move)
        topic.save()

    return topic


def send_message_mp(
        author,
        n_topic,
        text,
        send_by_mail=True,
        direct=False):
    """
    Send a post in an MP.
    Most of the param are obvious, excepted :
    * direct : send a mail directly without mp (ex : ban members who wont connect again)
    * leave : the author leave the conversation (usefull for the bot : it wont read the response a member could send)
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
    post.save()

    n_topic.last_message = post
    n_topic.save()

    if not direct:
        signals.new_content.send(sender=post.__class__, instance=post, by_email=send_by_mail)

    if send_by_mail and direct:
        subject = "{} : {}".format(settings.ZDS_APP['site']['litteral_name'], n_topic.title)
        from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                       settings.ZDS_APP['site']['email_noreply'])
        for part in n_topic.participants.all():
            message_html = render_to_string('email/direct.html', {'msg': emarkdown(text)})
            message_txt = render_to_string('email/direct.txt', {'msg': text})

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [part.email])
            msg.attach_alternative(message_html, "text/html")
            try:
                msg.send()
            except:
                msg = None

    return n_topic
