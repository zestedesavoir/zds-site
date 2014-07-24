# coding: utf-8

from datetime import datetime
from zds.forum.models import Topic, Post, follow
from zds.forum.views import get_tag_by_title
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from zds.utils.templatetags.emarkdown import emarkdown

def create_topic(
        author,
        forum,
        title,
        subtitle,
        text,
        key):
    """create topic in forum"""
    
    (tags, title_only) = get_tag_by_title(title[:80])

    # Creating the thread
    n_topic = Topic()
    n_topic.forum = forum
    n_topic.title = title_only
    n_topic.subtitle = subtitle
    n_topic.pubdate = datetime.now()
    n_topic.author = author
    n_topic.key = key
    n_topic.save()
    n_topic.add_tags(tags)
    n_topic.save()

    # Add the first message
    post = Post()
    post.topic = n_topic
    post.author = author
    post.text = text
    post.text_html = emarkdown(text)
    post.pubdate = datetime.now()
    post.position = 1
    post.save()

    n_topic.last_message = post
    n_topic.save()

    follow(n_topic, user=author)

    return n_topic

def send_post(topic, text):
    
    post = Post()
    post.topic = topic
    post.author = topic.author
    post.text = text
    post.text_html = emarkdown(text)
    post.pubdate = datetime.now()
    post.position = topic.last_message.position+1
    post.save()
    
    topic.last_message = post
    topic.save()

def lock_topic(topic):
    topic.is_locked = True
    topic.save()

def unlock_topic(topic):
    topic.is_locked = False
    topic.save()
    
