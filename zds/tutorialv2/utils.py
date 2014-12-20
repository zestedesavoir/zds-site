# coding: utf-8

from zds.tutorialv2.models import PubliableContent, ContentRead
from zds import settings
from zds.utils import get_current_user

def get_last_tutorials():
    """get the last issued tutorials"""
    n = settings.ZDS_APP['tutorial']['home_number']
    tutorials = PubliableContent.objects.all()\
        .exclude(type="ARTICLE")\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:n]

    return tutorials


def get_last_articles():
    """get the last issued articles"""
    n = settings.ZDS_APP['tutorial']['home_number']
    articles = PubliableContent.objects.all()\
        .exclude(type="TUTO")\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:n]

    return articles


def never_read(tutorial, user=None):
    """Check if a topic has been read by an user since it last post was
    added."""
    if user is None:
        user = get_current_user()

    return ContentRead.objects\
        .filter(note=tutorial.last_note, tutorial=tutorial, user=user)\
        .count() == 0


def mark_read(tutorial):
    """Mark a tutorial as read for the user."""
    if tutorial.last_note is not None:
        ContentRead.objects.filter(
            tutorial=tutorial,
            user=get_current_user()).delete()
        a = ContentRead(
            note=tutorial.last_note,
            tutorial=tutorial,
            user=get_current_user())
        a.save()