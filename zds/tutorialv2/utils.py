# coding: utf-8

import shutil
import os
from datetime import datetime
import copy

from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

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


def get_target_tagged_tree_for_container(movable_child, root, bias=-1):
    """Gets the tagged tree with displacement availability when movable_child is an extract

    :param movable_child: the container we want to move
    :param root: the VersionnedContent we use as root
    :param bias: a negative or zero integer that represent the level bias. A value of -1 (default) represent
    the fact that we want to make the *movable_child* **a sibling** of the tagged child, a value of 0 that we want
    to make it a sub child.
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
            level = movable_child.get_tree_level()

            enabled = child != movable_child and child != root
            if bias == -1 and child.parent is not None:
                tested = child.parent
            else:
                tested = child
            enabled = enabled and tested.can_add_container()
            if level > 2:
                enabled = enabled and tested == root

            target_tagged_tree.append((child.get_path(True), child.title, child.get_tree_depth(), enabled))

    return target_tagged_tree


class FailureDuringPublication(Exception):
    """Exception raised if something goes wrong during publication process
    """

    def __init__(self, *args, **kwargs):
        super(FailureDuringPublication, self).__init__(*args, **kwargs)


def publish_container(db_object, base_dir, container):
    """ "Publish" a given container, in a recursive way

    :param db_object: database representation of the content
    :type db_object: PublishableContent
    :param base_dir: directory of the top container
    :type base_dir: str
    :param container: a given container
    :type container: Container
    :raise FailureDuringPublication: if anything goes wrong
    """

    # TODO: images stuff !!

    template = 'tutorialv2/export/chapter.html'

    # jsFiddle support
    if db_object.js_support:
        is_js = "js"
    else:
        is_js = ""

    current_dir = os.path.dirname(os.path.join(base_dir, container.get_prod_path(relative=True)))

    if not os.path.isdir(current_dir):
        os.makedirs(current_dir)

    if container.has_extracts():  # the container can be rendered in one template
        parsed = render_to_string(template, {'container': container, 'is_js': is_js})
        f = open(os.path.join(base_dir, container.get_prod_path(relative=True)), 'w')

        try:
            f.write(parsed.encode('utf-8'))
        except (UnicodeError, UnicodeEncodeError):
            raise FailureDuringPublication(
                _(u'Une erreur est survenue durant la publication de « {} », vérifiez le code markdown')
                .format(container.title))

        f.close()

        for extract in container.children:
            extract.text = None

        container.introduction = None
        container.conclusion = None

    else:  # separate render of introduction and conclusion

        current_dir = os.path.join(base_dir, container.get_prod_path(relative=True))  # create subdirectory

        if not os.path.isdir(current_dir):
            os.makedirs(current_dir)

        if container.introduction:
            path = os.path.join(container.get_prod_path(relative=True), 'introduction.html')
            f = open(os.path.join(base_dir, path), 'w')

            try:
                f.write(emarkdown(container.get_introduction(), db_object.js_support))
            except (UnicodeError, UnicodeEncodeError):
                raise FailureDuringPublication(
                    _(u'Une erreur est survenue durant la publication de l\'introduction de « {} »,'
                      u' vérifiez le code markdown').format(container.title))

            container.introduction = path

        if container.conclusion:
            path = os.path.join(container.get_prod_path(relative=True), 'conclusion.html')
            f = open(os.path.join(base_dir, path), 'w')

            try:
                f.write(emarkdown(container.get_conclusion(), db_object.js_support))
            except (UnicodeError, UnicodeEncodeError):
                raise FailureDuringPublication(
                    _(u'Une erreur est survenue durant la publication de la conclusion de « {} »,'
                      u' vérifiez le code markdown').format(container.title))

            container.conclusion = path

        for child in container.children:
            publish_container(db_object, base_dir, child)


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

    if is_major_update:
        versioned.pubdate = datetime.now()

    # First write the files in a temporary directory: if anything goes wrong,
    # the last published version is not impacted !
    tmp_path = os.path.join(settings.ZDS_APP['content']['repo_public_path'], versioned.slug + '__building')

    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)  # erase previous attempt, if any

    # render HTML:
    altered_version = copy.deepcopy(versioned)
    publish_container(db_object, tmp_path, altered_version)
    altered_version.dump_json(os.path.join(tmp_path, 'manifest.json'))

    # make room for "extra contents"
    extra_contents_path = os.path.join(tmp_path, settings.ZDS_APP['content']['extra_contents_dirname'])
    os.makedirs(extra_contents_path)

    base_name = os.path.join(extra_contents_path, versioned.slug)

    # 1. markdown file (base for the others) :
    parsed = render_to_string('tutorialv2/export/content.md', {'content': versioned})
    md_file_path = base_name + '.md'
    md_file = open(md_file_path, 'w')
    try:
        md_file.write(parsed.encode('utf-8'))
    except (UnicodeError, UnicodeEncodeError):
        raise FailureDuringPublication(_(u'Une erreur est survenue durant la génération du fichier markdown '
                                         u'à télécharger, vérifiez le code markdown'))
    md_file.close()

    pandoc_debug_str = ""
    if settings.PANDOC_LOG_STATE:
        pandoc_debug_str = " 2>&1 | tee -a " + settings.PANDOC_LOG

    os.chdir(extra_contents_path)  # for pandoc

    # 2. HTML
    os.system(
        settings.PANDOC_LOC + "pandoc -s -S --toc " + md_file_path + " -o " + base_name + ".html" + pandoc_debug_str)
    # 3. epub
    os.system(
        settings.PANDOC_LOC + "pandoc -s -S --toc " + md_file_path + " -o " + base_name + ".epub" + pandoc_debug_str)
    # 4. PDF
    os.system(
        settings.PANDOC_LOC + "pandoc " + settings.PANDOC_PDF_PARAM + " " +
        md_file_path + " -o " + base_name + ".pdf" + pandoc_debug_str)

    os.chdir(settings.BASE_DIR)

    # ok, now we can really publish the thing !
    if db_object.public_version:
        public_version = db_object.public_version

        # the content have been published in the past, so clean old files !
        old_path = public_version.get_prod_path()
        shutil.rmtree(old_path)

    else:
        public_version = PublishedContent()

    # make the new public version
    public_version.content_public_slug = versioned.slug
    public_version.content_type = versioned.type
    public_version.content_pk = db_object.pk
    public_version.content = db_object
    public_version.save()

    # move the stuffs into the good position
    shutil.move(tmp_path, public_version.get_prod_path())

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

        db_object.public_version = None
        db_object.save()

        return True

    except (ObjectDoesNotExist, IOError):
        pass

    return False
