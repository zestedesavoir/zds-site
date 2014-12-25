# coding: utf-8

from zds.tutorialv2.models import PublishableContent, ContentRead
from zds import settings
from zds.utils import get_current_user


def get_last_tutorials():
    """
    :return: last issued tutorials
    """
    n = settings.ZDS_APP['tutorial']['home_number']
    tutorials = PublishableContent.objects.all()\
        .exclude(type="ARTICLE")\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:n]

    return tutorials


def get_last_articles():
    """
    :return: last issued articles
    """
    n = settings.ZDS_APP['tutorial']['home_number']
    articles = PublishableContent.objects.all()\
        .exclude(type="TUTO")\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:n]

    return articles


def never_read(content, user=None):
    """
    Check if a content note feed has been read by an user since its last post was added.
    :param content: the content to check
    :return: `True` if it is the case, `False` otherwise
    """
    if user is None:
        user = get_current_user()

    return ContentRead.objects\
        .filter(note=content.last_note, content=content, user=user)\
        .count() == 0


def mark_read(content):
    """
    Mark the last tutorial note as read for the user.
    :param content: the content to mark
    """
    if content.last_note is not None:
        ContentRead.objects.filter(
            content=content,
            user=get_current_user()).delete()
        a = ContentRead(
            note=content.last_note,
            content=content,
            user=get_current_user())
        a.save()
