# coding: utf-8
from django.http import Http404

from zds.tutorialv2.models import PublishableContent, ContentRead, Container, Extract
from zds import settings
from zds.utils import get_current_user


class TooDeepContainerError(ValueError):
    """
    Exception used to represent the fact you can't add a container to a level greater than two
    """

    def __init__(self, *args, **kwargs):
        super(TooDeepContainerError, self).__init__(*args, **kwargs)


def search_container_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` keys
    or the string representation
    :return: the Container object we were searching for
    :raise Http404 if no suitable container is found
    """
    container = None
    if isinstance(kwargs_array, str):
        dic = {}
        dic["parent_container_slug"] = kwargs_array.split("/")[0]
        if len(kwargs_array.split("/")) == 2:
            dic["container_slug"] = kwargs_array.split("/")[1]
        kwargs_array = dic

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


def try_adopt_new_child(adoptive_parent, child):
    """
    Try the adoptive parent to take the responsability of the child
    :param parent_full_path:
    :param child_slug:
    :param root:
    :raise Http404: if adoptive_parent_full_path is not found on root hierarchy
    :raise TypeError: if the adoptive parent is not allowed to adopt the child due to its type
    :raise TooDeepContainerError: if the child is a container that is too deep to be adopted by the proposed parent
    :return:
    """
    container = adoptive_parent
    if isinstance(child, Extract):
        if not container.can_add_extract():
            raise TypeError
        child.repo_delete('', False)
        container.add_extract(child, generate_slug=False)
    if isinstance(child, Container):
        if not container.can_add_container():
            raise TypeError
        if container.get_tree_depth() + child.get_tree_depth() > settings.ZDS_APP['content']['max_tree_depth']:
            raise TooDeepContainerError
        child.repo_delete('', False)
        container.add_container(child)

