# coding: utf-8

from datetime import datetime
from zds.mp.models import PrivateTopic, PrivatePost
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from zds.utils.templatetags.emarkdown import emarkdown

def send_mp(author, users, title, subtitle, text, send_by_mail=True, leave=True, direct=False):
    """
    Send MP at members
    """
    
    # Creating the thread
    n_topic = PrivateTopic()
    n_topic.title = title
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
    post.pubdate = datetime.now()
    post.position_in_topic = 1
    post.save()
    
    n_topic.last_message = post
    n_topic.save()
    
        # send email
    if send_by_mail:
        if direct :
            subject = "ZDS : " + n_topic.title
            from_email = 'ZesteDeSavoir <noreply@zestedesavoir.com>'
            for part in users:
                message_html = get_template('email/mp_direct.html').render(
                    Context({
                        'msg': emarkdown(text)
                    })
                )
                message_txt = get_template('email/mp_direct.txt').render(
                    Context({
                        'msg': text
                    })
                )
        
                msg = EmailMultiAlternatives(
                    subject, message_txt, from_email, [
                        part.email])
                msg.attach_alternative(message_html, "text/html")
                try :
                    msg.send()
                except:
                    msg = None
        else:
            subject = "ZDS - MP: " + n_topic.title
            from_email = 'ZesteDeSavoir <noreply@zestedesavoir.com>'
            for part in users:
                message_html = get_template('email/mp.html').render(
                    Context({
                        'username': part.username,
                        'url': settings.SITE_URL + n_topic.get_absolute_url(),
                        'author': author.username
                    })
                )
                message_txt = get_template('email/mp.txt').render(
                    Context({
                        'username': part.username,
                        'url': settings.SITE_URL + n_topic.get_absolute_url(),
                        'author': author.username
                    })
                )
        
                msg = EmailMultiAlternatives(
                    subject, message_txt, from_email, [
                        part.email])
                msg.attach_alternative(message_html, "text/html")
                try :
                    msg.send()
                except:
                    msg = None
    if leave:
        move = n_topic.participants.first()
        n_topic.author = move
        n_topic.participants.remove(move)
        n_topic.save()

    return n_topic