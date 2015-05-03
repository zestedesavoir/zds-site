# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from zds.mp.models import PrivateTopic, PrivatePost
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

    # Addi the first message
    post = PrivatePost()
    post.privatetopic = n_topic
    post.author = author
    post.text = text
    post.text_html = emarkdown(text)
    post.pubdate = datetime.now()
    post.position_in_topic = 1
    post.save()

    n_topic.last_message = post
    n_topic.save()

    # send email
    if send_by_mail:
        if direct:
            subject = u"{} : {}".format(settings.ZDS_APP['site']['litteral_name'], n_topic.title)
            from_email = u"{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                           settings.ZDS_APP['site']['email_noreply'])
            for part in users:
                message_html = render_to_string('email/direct.html', {'msg': emarkdown(text)})
                message_txt = render_to_string('email/direct.txt', {'msg': text})

                msg = EmailMultiAlternatives(subject, message_txt, from_email, [part.email])
                msg.attach_alternative(message_html, "text/html")
                try:
                    msg.send()
                except:
                    msg = None
        else:
            subject = u"{} - {} : {}".format(settings.ZDS_APP['site']['litteral_name'],
                                             _(u'Message Privé'),
                                             n_topic.title)
            from_email = u"{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                           settings.ZDS_APP['site']['email_noreply'])
            for part in users:
                context = {
                    'username': part.username,
                    'url': settings.ZDS_APP['site']['url'] + n_topic.get_absolute_url(),
                    'author': author.username,
                    'site_name': settings.ZDS_APP['site']['litteral_name']
                }
                message_html = render_to_string('email/mp/new.html', context)
                message_txt = render_to_string('email/mp/new.txt', context)

                msg = EmailMultiAlternatives(subject, message_txt, from_email, [part.email])
                msg.attach_alternative(message_html, "text/html")
                try:
                    msg.send()
                except:
                    msg = None
    if leave:
        move = n_topic.participants.first()
        n_topic.author = move
        n_topic.participants.remove(move)
        n_topic.save()

    return n_topic
