# coding: utf-8
from django.http import Http404

from zds.tutorialv2.models import PublishableContent, ContentRead, Container, Extract
from zds import settings
from zds.utils import get_current_user


def search_container_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` keys
    :return: the Container object we were searching for
    :raise Http404 if no suitable container is found
    """
    container = None

    if 'parent_container_slug' in kwargs_array:
            try:
                container = base_content.children_dict[kwargs_array['parent_container_slug']]
            except KeyError:
                raise Http404
            else:
                if not isinstance(container, Container):
                    raise Http404
    else:
        container = base_content

    # if extract is at depth 2 or 3 we get its direct parent container
    if 'container_slug' in kwargs_array:
        try:
            container = container.children_dict[kwargs_array['container_slug']]
        except KeyError:
            raise Http404
        else:
            if not isinstance(container, Container):
                raise Http404
    else:
        # if we have no subcontainer, there is neither "container_slug" nor "parent_container_slug
        return base_content
    if container is None:
        raise Http404
    return container


def search_extract_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` and MUST contains
    `extract_slug`
    :return: the Extract object
    :raise: Http404 if not found
    """
    # if the extract is at a depth of 3 we get the first parent container
    container = search_container_or_404(base_content, kwargs_array)

    extract = None
    if 'extract_slug' in kwargs_array:
        try:
            extract = container.children_dict[kwargs_array['extract_slug']]
        except KeyError:
            raise Http404
        else:
            if not isinstance(extract, Extract):
                raise Http404
    return extract


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
