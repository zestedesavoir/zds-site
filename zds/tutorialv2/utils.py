# coding: utf-8

import shutil
import os
from datetime import datetime

from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string

from zds.tutorialv2.models import PublishableContent, ContentRead, Container, Extract, PublishedContent
from zds import settings
from zds.utils import get_current_user
from zds.utils.templatetags.emarkdown import emarkdown


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
    if isinstance(kwargs_array, basestring):
        dic = {}
        dic["parent_container_slug"] = kwargs_array.split("/")[0]
        if len(kwargs_array.split("/")) >= 2:
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
    elif container == base_content:
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
    """Check if a content note feed has been read by an user since its last post was added.

    :param content: the content to check
    :return: `True` if it is the case, `False` otherwise
    """
    if user is None:
        user = get_current_user()

    return ContentRead.objects\
        .filter(note=content.last_note, content=content, user=user)\
        .count() == 0


def mark_read(content):
    """Mark the last tutorial note as read for the user.

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
    """Try the adoptive parent to take the responsability of the child

    :param parent_full_path:
    :param child_slug:
    :param root:
    :raise Http404: if adoptive_parent_full_path is not found on root hierarchy
    :raise TypeError: if the adoptive parent is not allowed to adopt the child due to its type
    :raise TooDeepContainerError: if the child is a container that is too deep to be adopted by the proposed parent
    """

    if isinstance(child, Extract):
        if not adoptive_parent.can_add_extract():
            raise TypeError
    if isinstance(child, Container):
        if not adoptive_parent.can_add_container():
            raise TypeError
        if adoptive_parent.get_tree_depth() + child.get_tree_level() > settings.ZDS_APP['content']['max_tree_depth']:
            raise TooDeepContainerError
    adoptive_parent.top_container().change_child_directory(child, adoptive_parent)


def get_target_tagged_tree(movable_child, root):
    """Gets the tagged tree with deplacement availability

    :param movable_child: the extract we want to move
    :param root: the VersionnedContent we use as root
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child
    check get_target_tagged_tree_for_extract and get_target_tagged_tree_for_container for format
    """
    if isinstance(movable_child, Extract):
        return get_target_tagged_tree_for_extract(movable_child, root)
    else:
        return get_target_tagged_tree_for_container(movable_child, root)


def get_target_tagged_tree_for_extract(movable_child, root):
    """Gets the tagged tree with displacement availability when movable_child is an extract

    :param movable_child: the extract we want to move
    :param root: the VersionnedContent we use as root
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child
    tuples are ``(relative_path, title, level, can_be_a_target)``
    """
    target_tagged_tree = []
    for child in root.traverse(False):
        if isinstance(child, Extract):
            target_tagged_tree.append((child.get_full_slug(),
                                       child.title, child.get_tree_depth(), child != movable_child))
        else:
            target_tagged_tree.append((child.get_path(True), child.title, child.get_tree_depth(), False))

    return target_tagged_tree


def get_target_tagged_tree_for_container(movable_child, root):
    """Gets the tagged tree with displacement availability when movable_child is an extract

    :param movable_child: the container we want to move
    :param root: the VersionnedContent we use as root
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child
    extracts are not included
    """
    target_tagged_tree = []
    for child in root.traverse(True):
        if child.get_path(False) == root.get_path(False):
            continue
        if child.parent.get_path(False) == movable_child.get_path(False):
            target_tagged_tree.append((child.get_path(True), child.title, child.get_tree_level(), False))
        else:
            composed_depth = child.get_tree_depth() + movable_child.get_tree_depth()
            enabled = composed_depth <= settings.ZDS_APP['content']['max_tree_depth']
            target_tagged_tree.append((child.get_path(True), child.title, child.get_tree_level(),
                                       enabled and child != movable_child and child != root))

    return target_tagged_tree


class FailureDuringPublication(Exception):
    """Exception raised if something goes wrong during publication process
    """

    def __init__(self, *args, **kwargs):
        super(FailureDuringPublication, self).__init__(*args, **kwargs)


def publish_content(db_object, versioned, is_major_update=True):
    """Publish a given content.

    Note: create a manifest.json without the introduction and conclusion if not needed. Also remove the "text" field
    of extracts.

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :param versioned: version of the content to publish
    :type versioned: VersionedContent
    :param is_major_update: if set to `True`, will update the publication date
    :type is_major_update: bool
    :raise FailureDuringPublication: if something goes wrong
    :return: the published representation
    :rtype: PublishedContent
    """

    # TODO: to avoid errors, some part of this function can be written in a recursive way !

    try:
        public_version = PublishedContent.objects.get(content=db_object)

        # the content have been published in the past, so clean old files
        old_path = public_version.get_prod_path()
        shutil.rmtree(old_path)

    except ObjectDoesNotExist:
        public_version = PublishedContent()

    # make the new public version
    public_version.content_public_slug = versioned.slug
    public_version.content_type = versioned.type
    public_version.content_pk = db_object.pk
    public_version.content = db_object
    public_version.save()

    # create directory(ies)
    repo_path = public_version.get_prod_path()
    os.makedirs(repo_path)

    template = 'tutorialv2/includes/container_online_template.part.html'
    # TODO: image stuff
    # TODO: jsfidle

    # write the files:
    if versioned.has_extracts():  # it's an article or a mini-tutorial
        parsed = render_to_string(template, {'container': versioned})
        f = open(versioned.get_prod_path(), 'w')
        f.write(parsed.encode('utf-8'))
        f.close()

        for extract in versioned.children:
            extract.text = None

        versioned.introduction = None
        versioned.conclusion = None

    else:  # it's another kind of tutorial

        # we need to write introduction and conclusion in a separate file
        if versioned.introduction:
            f = open(os.path.join(repo_path, 'introduction.html'), 'w')
            f.write(emarkdown(versioned.get_introduction()))
            versioned.introduction = 'introduction.html'
        if versioned.conclusion:
            f = open(os.path.join(repo_path, 'conclusion.html'), 'w')
            f.write(emarkdown(versioned.get_conclusion()))
            versioned.conclusion = 'conclusion.html'

        for child in versioned.children:
            if child.has_extracts():  # it's a middle-size tutorial
                parsed = render_to_string(template, {'container': child})
                f = open(child.get_prod_path(), 'w')
                f.write(parsed.encode('utf-8'))
                f.close()

                for extract in child.children:
                    extract.text = None

                child.introduction = None
                child.conclusion = None

            else:  # it's a big-tutorial
                directory = child.get_prod_path()
                if not os.path.exists(directory):
                    os.makedirs(directory)

                if child.introduction:
                    path = os.path.join(child.get_path(relative=True), 'introduction.html')
                    f = open(os.path.join(repo_path, path), 'w')
                    f.write(emarkdown(child.get_introduction()))
                    child.introduction = path
                if child.conclusion:
                    path = os.path.join(child.get_path(relative=True), 'conclusion.html')
                    f = open(os.path.join(repo_path, path), 'w')
                    f.write(emarkdown(child.get_conclusion()))
                    child.conclusion = path

                for chapter in child.children:
                    parsed = render_to_string(template, {'container': chapter})
                    f = open(chapter.get_prod_path(), 'w')
                    f.write(parsed.encode('utf-8'))
                    f.close()

                    for extract in chapter.children:
                        extract.text = None

                    chapter.introduction = None
                    chapter.conclusion = None

    versioned.dump_json(os.path.join(repo_path, 'manifest.json'))

    # save public version
    if is_major_update:
        public_version.publication_date = datetime.now()

    public_version.sha_public = versioned.current_version
    public_version.save()

    return public_version


def unpublish_content(db_object):
    """Remove the given content from the public view

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :return; `True` if unpublished, `False otherwise`
    """

    try:
        public_version = PublishedContent.objects.get(content=db_object)

        # clean files
        old_path = public_version.get_prod_path()

        if os.path.exists(old_path):
            shutil.rmtree(old_path)

        # remove public_version:
        public_version.delete()

        return True

    except (ObjectDoesNotExist, IOError):
        pass

    return False
