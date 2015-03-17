# coding: utf-8

from math import ceil
import shutil
from django.http import Http404
from gitdb.exc import BadObject

try:
    import ujson as json_reader
except ImportError:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

import json as json_writer
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from datetime import datetime
from git.repo import Repo
from git import Actor
from django.core.exceptions import PermissionDenied

from zds.gallery.models import Image, Gallery
from zds.utils import slugify, get_current_user
from zds.utils.models import SubCategory, Licence, Comment
from zds.utils.tutorials import get_blob
from zds.utils.tutorialv2 import export_content
from zds.settings import ZDS_APP
from zds.utils.models import HelpWriting
from uuslug import uuslug


TYPE_CHOICES = (
    ('TUTORIAL', 'Tutoriel'),
    ('ARTICLE', 'Article'),
)

STATUS_CHOICES = (
    ('PENDING', 'En attente d\'un validateur'),
    ('PENDING_V', 'En cours de validation'),
    ('ACCEPT', 'Publié'),
    ('REJECT', 'Rejeté'),
)


class InvalidOperationError(RuntimeError):
    pass


class Container:
    """
    A container, which can have sub-Containers or Extracts.

    A Container has a title, a introduction and a conclusion, a parent (which can be None) and a position into this
    parent (which is 1 by default).

    It has also a tree depth.

    A container could be either a tutorial/article, a part or a chapter.
    """

    title = ''
    slug = ''
    introduction = None
    conclusion = None
    parent = None
    position_in_parent = 1
    children = []
    children_dict = {}
    slug_pool = {}

    # TODO: thumbnails ?

    def __init__(self, title, slug='', parent=None, position_in_parent=1):
        self.title = title
        self.slug = slug
        self.parent = parent
        self.position_in_parent = position_in_parent

        self.children = []  # even if you want, do NOT remove this line
        self.children_dict = {}

        self.slug_pool = {'introduction': 1, 'conclusion': 1}  # forbidden slugs

    def __unicode__(self):
        return u'<Conteneur \'{}\'>'.format(self.title)

    def has_extracts(self):
        """
        Note : this function rely on the fact that the children can only be of one type.
        :return: `True` if the container has extract as children, `False` otherwise.
        """
        if len(self.children) == 0:
            return False
        return isinstance(self.children[0], Extract)

    def has_sub_containers(self):
        """
        Note : this function rely on the fact that the children can only be of one type.
        :return: `True` if the container has containers as children, `False` otherwise.
        """
        if len(self.children) == 0:
            return False
        return isinstance(self.children[0], Container)

    def get_last_child_position(self):
        """
        :return: the position of the last child
        """
        return len(self.children)

    def get_tree_depth(self):
        """
        Tree depth is no more than 2, because there is 3 levels for Containers :
        - PublishableContent (0),
        - Part (1),
        - Chapter (2)
        Note that `'max_tree_depth` is `2` to ensure that there is no more than 3 levels
        :return: Tree depth
        """
        depth = 0
        current = self
        while current.parent is not None:
            current = current.parent
            depth += 1
        return depth

    def top_container(self):
        """
        :return: Top container (for which parent is `None`)
        """
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def get_unique_slug(self, title):
        """
        Generate a slug from title, and check if it is already in slug pool. If it is the case, recursively add a
        "-x" to the end, where "x" is a number starting from 1. When generated, it is added to the slug pool.
        :param title: title from which the slug is generated (with `slugify()`)
        :return: the unique slug
        """
        base = slugify(title)
        try:
            n = self.slug_pool[base]
        except KeyError:
            new_slug = base
            self.slug_pool[base] = 0
        else:
            new_slug = base + '-' + str(n)
        self.slug_pool[base] += 1
        self.slug_pool[new_slug] = 1
        return new_slug

    def add_slug_to_pool(self, slug):
        """
        Add a slug to the slug pool to be taken into account when generate a unique slug
        :param slug: the slug to add
        """
        try:
            self.slug_pool[slug]  # test access
        except KeyError:
            self.slug_pool[slug] = 1
        else:
            raise Exception('slug "{}" already in the slug pool !'.format(slug))

    def long_slug(self):
        """
        :return: a long slug that embed slugs of parents
        """
        long_slug = ''
        if self.parent:
            long_slug = self.parent.long_slug() + '__'
        return long_slug + self.slug

    def can_add_container(self):
        """
        :return: True if this container accept child container, false otherwise
        """
        if not self.has_extracts():
            if self.get_tree_depth() < ZDS_APP['content']['max_tree_depth'] - 1:
                if not self.top_container().is_article:
                    return True
        return False

    def can_add_extract(self):
        """
        :return: True if this container accept child extract, false otherwise
        """
        if not self.has_sub_containers():
            if self.get_tree_depth() <= ZDS_APP['content']['max_tree_depth']:
                return True
        return False

    def add_container(self, container, generate_slug=False):
        """
        Add a child Container, but only if no extract were previously added and tree depth is < 2.
        Note: this function will also raise an Exception if article, because it cannot contain child container
        :param container: the new container
        :param generate_slug: if `True`, ask the top container an unique slug for this object
        """
        if self.can_add_container():
            if generate_slug:
                container.slug = self.get_unique_slug(container.title)
            else:
                self.add_slug_to_pool(container.slug)
            container.parent = self
            container.position_in_parent = self.get_last_child_position() + 1
            self.children.append(container)
            self.children_dict[container.slug] = container
        else:
            raise InvalidOperationError("Cannot add another level to this container")

    def add_extract(self, extract, generate_slug=False):
        """
        Add a child container, but only if no container were previously added
        :param extract: the new extract
        :param generate_slug: if `True`, ask the top container an unique slug for this object
        """
        if self.can_add_extract():
            if generate_slug:
                extract.slug = self.get_unique_slug(extract.title)
            else:
                self.add_slug_to_pool(extract.slug)
            extract.container = self
            extract.position_in_parent = self.get_last_child_position() + 1
            self.children.append(extract)
            self.children_dict[extract.slug] = extract
        else:
            raise InvalidOperationError("Can't add an extract if this container already contains containers.")

    def update_children(self):
        """
        Update the path for introduction and conclusion for the container and all its children. If the children is an
        extract, update the path to the text instead. This function is useful when `self.slug` has
        changed.
        Note : this function does not account for a different arrangement of the files.
        """
        # TODO : path comparison instead of pure rewritring ?
        self.introduction = os.path.join(self.get_path(relative=True), "introduction.md")
        self.conclusion = os.path.join(self.get_path(relative=True), "conclusion.md")
        for child in self.children:
            if isinstance(child, Container):
                child.update_children()
            elif isinstance(child, Extract):
                child.text = child.get_path(relative=True)
        # TODO : does this function should also rewrite `slug_pool` ?

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the container.
        Note: this function rely on the fact that the top container is VersionedContainer.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        base = ''
        if self.parent:
            base = self.parent.get_path(relative=relative)
        return os.path.join(base, self.slug)

    def get_prod_path(self):
        """
        Get the physical path to the public version of the container.
        Note: this function rely on the fact that the top container is VersionedContainer.
        :return: physical path
        """
        base = ''
        if self.parent:
            base = self.parent.get_prod_path()
        return os.path.join(base, self.slug)

    def get_absolute_url(self):
        """
        :return: url to access the container
        """
        return self.top_container().get_absolute_url() + self.get_path(relative=True) + '/'

    def get_edit_url(self):
        """
        :return: url to edit the container
        """
        slugs = [self.slug]
        parent = self.parent
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.top_container().pk]
        args.extend(slugs)

        return reverse('content:edit-container', args=args)

    def get_delete_url(self):
        """
        :return: url to edit the container
        """
        slugs = [self.slug]
        parent = self.parent
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.top_container().pk]
        args.extend(slugs)

        return reverse('content:delete', args=args)

    def get_introduction(self):
        """
        :return: the introduction from the file in `self.introduction`
        """
        if self.introduction:
            return get_blob(self.top_container().repository.commit(self.top_container().current_version).tree,
                            self.introduction)

    def get_conclusion(self):
        """
        :return: the conclusion from the file in `self.conclusion`
        """
        if self.introduction:
            return get_blob(self.top_container().repository.commit(self.top_container().current_version).tree,
                            self.conclusion)

    def repo_update(self, title, introduction, conclusion, commit_message=''):
        """
        Update the container information and commit them into the repository
        :param title: the new title
        :param introduction: the new introduction text
        :param conclusion: the new conclusion text
        :param commit_message: commit message that will be used instead of the default one
        :return : commit sha
        """

        repo = self.top_container().repository

        # update title
        if title != self.title:
            self.title = title
            if self.get_tree_depth() > 0:  # if top container, slug is generated from DB, so already changed
                old_path = self.get_path(relative=True)
                self.slug = self.parent.get_unique_slug(title)
                new_path = self.get_path(relative=True)
                repo.index.move([old_path, new_path])

                # update manifest
                self.update_children()

        # update introduction and conclusion
        rel_path = self.get_path(relative=True)
        if self.introduction is None:
            self.introduction = os.path.join(rel_path, 'introduction.md')
        if self.conclusion is None:
            self.conclusion = os.path.join(rel_path, 'conclusion.md')

        path = self.top_container().get_path()
        f = open(os.path.join(path, self.introduction), "w")
        f.write(introduction.encode('utf-8'))
        f.close()
        f = open(os.path.join(path, self.conclusion), "w")
        f.write(conclusion.encode('utf-8'))
        f.close()

        self.top_container().dump_json()
        repo.index.add(['manifest.json', self.introduction, self.conclusion])

        if commit_message == '':
            commit_message = u'Mise à jour de « ' + self.title + u' »'
        cm = repo.index.commit(commit_message, **get_commit_author())

        self.top_container().sha_draft = cm.hexsha

        return cm.hexsha

    def repo_add_container(self, title, introduction, conclusion, commit_message=''):
        """
        :param title: title of the new container
        :param introduction: text of its introduction
        :param conclusion: text of its conclusion
        :param commit_message: commit message that will be used instead of the default one
        :return: commit sha
        """
        subcontainer = Container(title)

        # can a subcontainer be added ?
        try:
            self.add_container(subcontainer, generate_slug=True)
        except Exception:
            raise PermissionDenied

        # create directory
        repo = self.top_container().repository
        path = self.top_container().get_path()
        rel_path = subcontainer.get_path(relative=True)
        os.makedirs(os.path.join(path, rel_path), mode=0o777)

        repo.index.add([rel_path])

        # create introduction and conclusion
        subcontainer.introduction = os.path.join(rel_path, 'introduction.md')
        subcontainer.conclusion = os.path.join(rel_path, 'conclusion.md')

        f = open(os.path.join(path, subcontainer.introduction), "w")
        f.write(introduction.encode('utf-8'))
        f.close()
        f = open(os.path.join(path, subcontainer.conclusion), "w")
        f.write(conclusion.encode('utf-8'))
        f.close()

        # commit
        self.top_container().dump_json()
        repo.index.add(['manifest.json', subcontainer.introduction, subcontainer.conclusion])

        if commit_message == '':
            commit_message = u'Création du conteneur « ' + title + u' »'
        cm = repo.index.commit(commit_message, **get_commit_author())

        self.top_container().sha_draft = cm.hexsha

        return cm.hexsha

    def repo_add_extract(self, title, text, commit_message=''):
        """
        :param title: title of the new extract
        :param text: text of the new extract
        :param commit_message: commit message that will be used instead of the default one
        :return: commit sha
        """
        extract = Extract(title)

        # can an extract be added ?
        try:
            self.add_extract(extract, generate_slug=True)
        except Exception:
            raise PermissionDenied

        # create text
        repo = self.top_container().repository
        path = self.top_container().get_path()

        extract.text = extract.get_path(relative=True)
        f = open(os.path.join(path, extract.text), "w")
        f.write(text.encode('utf-8'))
        f.close()

        # commit
        self.top_container().dump_json()
        repo.index.add(['manifest.json', extract.text])

        if commit_message == '':
            commit_message = u'Création de l\'extrait « ' + title + u' »'
        cm = repo.index.commit(commit_message, **get_commit_author())

        self.top_container().sha_draft = cm.hexsha

        return cm.hexsha

    def repo_delete(self, commit_message='', do_commit=True):
        """
        :param commit_message: commit message used instead of default one if provided
        :param do_commit: tells if we have to commit the change now or let the outter program do it
        :return: commit sha
        """
        path = self.get_path(relative=True)
        repo = self.top_container().repository
        repo.index.remove([path], r=True)
        shutil.rmtree(self.get_path())  # looks like removing from git is not enough !!

        # now, remove from manifest
        # work only if slug is correct
        top = self.parent
        top.children_dict.pop(self.slug)
        top.children.pop(top.children.index(self))

        # commit
        top.top_container().dump_json()
        repo.index.add(['manifest.json'])

        if commit_message == '':
            commit_message = u'Suppression du conteneur « {} »'.format(self.title)
        if do_commit:
            cm = repo.index.commit(commit_message, **get_commit_author())

            self.top_container().sha_draft = cm.hexsha

        return cm.hexsha

    def move_child_up(self, child_slug):
        """
        Change the child's ordering by moving up the child whose slug equals child_slug.
        This method **does not** automaticaly update the repo
        :param child_slug: the child's slug
        :raise ValueError: if the slug does not refer to an existing child
        :raise IndexError: if the extract is already the first child
        """
        if child_slug not in self.children_dict:
            raise ValueError(child_slug + " does not exist")
        child_pos = self.children.index(self.children_dict[child_slug])
        if child_pos == 0:
            raise IndexError(child_slug + " is the first element")
        self.children[child_pos], self.children[child_pos - 1] = self.children[child_pos - 1], self.children[child_pos]
        self.children[child_pos].position_in_parent = child_pos + 1
        self.children[child_pos - 1].position_in_parent = child_pos

    def move_child_down(self, child_slug):
        """
        Change the child's ordering by moving down the child whose slug equals child_slug.
        This method **does not** automaticaly update the repo
        :param child_slug: the child's slug
        :raise ValueError: if the slug does not refer to an existing child
        :raise IndexError: if the extract is already the last child
        """
        if child_slug not in self.children_dict:
            raise ValueError(child_slug + " does not exist")
        child_pos = self.children.index(self.children_dict[child_slug])
        if child_pos == len(self.children) - 1:
            raise IndexError(child_slug + " is the last element")
        self.children[child_pos], self.children[child_pos + 1] = self.children[child_pos + 1], self.children[child_pos]
        self.children[child_pos].position_in_parent = child_pos
        self.children[child_pos + 1].position_in_parent = child_pos + 1

    def move_child_after(self, child_slug, refer_slug):
        """
        Change the child's ordering by moving the child to be below the reference child.
        This method **does not** automaticaly update the repo
        :param child_slug: the child's slug
        :param refer_slug: the referent child's slug.
        :raise ValueError: if one slug does not refer to an existing child
        """
        if child_slug not in self.children_dict:
            raise ValueError(child_slug + " does not exist")
        if refer_slug not in self.children_dict:
            raise ValueError(refer_slug + " does not exist")
        child_pos = self.children.index(self.children_dict[child_slug])
        refer_pos = self.children.index(self.children_dict[refer_slug])

        # if we want our child to get down (reference is an lower child)
        if child_pos < refer_pos:
            for i in range(child_pos, refer_pos):
                self.move_child_down(child_slug)
        elif child_pos > refer_pos:
            # if we want our child to get up (reference is an upper child)
            for i in range(child_pos, refer_pos + 1, - 1):
                self.move_child_up(child_slug)

    def move_child_before(self, child_slug, refer_slug):
        """
        Change the child's ordering by moving the child to be just above the reference child. .
        This method **does not** automaticaly update the repo
        :param child_slug: the child's slug
        :param refer_slug: the referent child's slug.
        :raise ValueError: if one slug does not refer to an existing child
        """
        if child_slug not in self.children_dict:
            raise ValueError(child_slug + " does not exist")
        if refer_slug not in self.children_dict:
            raise ValueError(refer_slug + " does not exist")
        child_pos = self.children.index(self.children_dict[child_slug])
        refer_pos = self.children.index(self.children_dict[refer_slug])

        # if we want our child to get down (reference is an lower child)
        if child_pos < refer_pos:
            for i in range(child_pos, refer_pos - 1):
                self.move_child_down(child_slug)
        elif child_pos > refer_pos:
            # if we want our child to get up (reference is an upper child)
            for i in range(child_pos, refer_pos, - 1):
                self.move_child_up(child_slug)


class Extract:
    """
    A content extract from a Container.

    It has a title, a position in the parent container and a text.
    """

    title = ''
    slug = ''
    container = None
    position_in_parent = 1
    text = None

    def __init__(self, title, slug='', container=None, position_in_parent=1):
        self.title = title
        self.slug = slug
        self.container = container
        self.position_in_parent = position_in_parent

    def __unicode__(self):
        return u'<Extrait \'{}\'>'.format(self.title)

    def get_absolute_url(self):
        """
        :return: the url to access the tutorial offline
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url(),
            self.position_in_parent,
            self.slug
        )

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_online(),
            self.position_in_parent,
            self.slug
        )

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_beta(),
            self.position_in_parent,
            self.slug
        )

    def get_edit_url(self):
        """
        :return: url to edit the extract
        """
        slugs = [self.slug]
        parent = self.container
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.container.top_container().pk]
        args.extend(slugs)

        return reverse('content:edit-extract', args=args)

    def get_delete_url(self):
        """
        :return: url to delete the extract
        """
        slugs = [self.slug]
        parent = self.container
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.container.top_container().pk]
        args.extend(slugs)

        return reverse('content:delete', args=args)

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the extract.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        return os.path.join(self.container.get_path(relative=relative), self.slug) + '.md'

    def get_text(self):
        """
        :return: versioned text
        """
        if self.text:
            return get_blob(
                self.container.top_container().repository.commit(self.container.top_container().current_version).tree,
                self.text)

    def repo_update(self, title, text, commit_message=''):
        """
        :param title: new title of the extract
        :param text: new text of the extract
        :param commit_message: commit message that will be used instead of the default one
        :return: commit sha
        """

        repo = self.container.top_container().repository

        if title != self.title:
            # get a new slug
            old_path = self.get_path(relative=True)
            self.title = title
            self.slug = self.container.get_unique_slug(title)
            new_path = self.get_path(relative=True)
            # move file
            repo.index.move([old_path, new_path])

        # edit text
        path = self.container.top_container().get_path()

        self.text = self.get_path(relative=True)
        f = open(os.path.join(path, self.text), "w")
        f.write(text.encode('utf-8'))
        f.close()

        # commit
        self.container.top_container().dump_json()
        repo.index.add(['manifest.json', self.text])

        if commit_message == '':
            commit_message = u'Modification de l\'extrait « {} », situé dans le conteneur « {} »'\
                .format(self.title, self.container.title)
        cm = repo.index.commit(commit_message, **get_commit_author())

        self.container.top_container().sha_draft = cm.hexsha

        return cm.hexsha

    def repo_delete(self, commit_message='', do_commit=True):
        """
        :param commit_message: commit message used instead of default one if provided
        :param do_commit: tells if we have to commit the change now or let the outter program do it
        :return: commit sha
        """
        path = self.get_path(relative=True)
        repo = self.container.top_container().repository
        repo.index.remove([path])
        os.remove(self.get_path())  # looks like removing from git is not enough

        # now, remove from manifest
        # work only if slug is correct!!
        top = self.container
        top.children_dict.pop(self.slug, None)
        top.children.pop(top.children.index(self))

        # commit
        top.top_container().dump_json()
        repo.index.add(['manifest.json'])

        if commit_message == '':
            commit_message = u'Suppression de l\'extrait « {} »'.format(self.title)
        if do_commit:
            cm = repo.index.commit(commit_message, **get_commit_author())

            self.container.top_container().sha_draft = cm.hexsha

        return cm.hexsha


class VersionedContent(Container):
    """
    This class is used to handle a specific version of a tutorial.tutorial

    It is created from the "manifest.json" file, and could dump information in it.

    For simplicity, it also contains DB information (but cannot modified them!), filled at the creation.
    """

    current_version = None
    repository = None

    # Metadata from json :
    description = ''
    type = ''
    licence = None

    # Metadata from DB :
    pk = 0
    sha_draft = None
    sha_beta = None
    sha_public = None
    sha_validation = None
    is_beta = False
    is_validation = False
    is_public = False
    in_beta = False
    in_validation = False
    in_public = False

    is_article = False
    is_tutorial = False

    have_markdown = False
    have_html = False
    have_pdf = False
    have_epub = False

    authors = None
    subcategory = None
    image = None
    creation_date = None
    pubdate = None
    update_date = None
    source = None

    def __init__(self, current_version, _type, title, slug):
        Container.__init__(self, title, slug)
        self.current_version = current_version
        self.type = _type

        if os.path.exists(self.get_path()):
            self.repository = Repo(self.get_path())

    def __unicode__(self):
        return self.title

    def get_absolute_url(self, version=None):
        """
        :return: the url to access the tutorial when offline
        """
        url = reverse('content:view', args=[self.pk, self.slug])

        if version and version != self.sha_draft:
            url += '?version=' + version

        return url

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return reverse('zds.tutorialv2.views.view_tutorial_online', args=[self.slug])

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        """
        if self.in_beta:
            return self.get_absolute_url() + '?version=' + self.sha_beta
        else:
            return self.get_absolute_url()

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the Content.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        if relative:
            return ''
        else:
            return os.path.join(settings.ZDS_APP['content']['repo_private_path'], self.slug)

    def get_prod_path(self):
        """
        Get the physical path to the public version of the content
        :return: physical path
        """
        return os.path.join(settings.ZDS_APP['content']['repo_public_path'], self.slug)

    def get_list_of_chapters(self):
        """
        :return: a list of chpaters (Container which contains Extracts) in the reading order
        """
        continuous_list = []
        if not self.is_article:  # article cannot be paginated
            if len(self.children) != 0 and isinstance(self.children[0], Container):  # children must be Containers !
                for child in self.children:
                    if len(child.children) != 0:
                        if isinstance(child.children[0], Extract):
                            continuous_list.append(child)  # it contains Extract, this is a chapter, so paginated
                        else:  # Container is a part
                            for sub_child in child.children:
                                continuous_list.append(sub_child)  # even if empty `sub_child.childreen`, it's chapter
        return continuous_list

    def get_json(self):
        """
        :return: raw JSON file
        """
        dct = export_content(self)
        data = json_writer.dumps(dct, indent=4, ensure_ascii=False)
        return data

    def dump_json(self, path=None):
        """
        Write the JSON into file
        :param path: path to the file. If `None`, write in "manifest.json"
        """
        if path is None:
            man_path = os.path.join(self.get_path(), 'manifest.json')
        else:
            man_path = path

        json_data = open(man_path, "w")
        json_data.write(self.get_json().encode('utf-8'))
        json_data.close()

    def repo_update_top_container(self, title, slug, introduction, conclusion, commit_message=''):
        """
        Update the top container information and commit them into the repository.
        Note that this is slightly different from the `repo_update()` function, because slug is generated using DB
        :param title: the new title
        :param slug: the new slug, according to title (choose using DB!!)
        :param introduction: the new introduction text
        :param conclusion: the new conclusion text
        :param commit_message: commit message that will be used instead of the default one
        :return : commit sha
        """

        if slug != self.slug:
            # move repository
            old_path = self.get_path()
            self.slug = slug
            new_path = self.get_path()
            shutil.move(old_path, new_path)
            self.repository = Repo(new_path)

        return self.repo_update(title, introduction, conclusion, commit_message)


def get_content_from_json(json, sha):
    """
    Transform the JSON formated data into `VersionedContent`
    :param json: JSON data from a `manifest.json` file
    :param sha: version
    :return: a `VersionedContent` with all the information retrieved from JSON
    """
    # TODO: should definitely be static
    # create and fill the container
    versioned = VersionedContent(sha, 'TUTORIAL', json['title'], json['slug'])

    if 'version' in json and json['version'] == 2:
        # fill metadata :
        if 'description' in json:
            versioned.description = json['description']

        if 'type' in json:
            if json['type'] == 'ARTICLE' or json['type'] == 'TUTORIAL':
                versioned.type = json['type']

        if 'licence' in json:
            versioned.licence = Licence.objects.filter(code=json['licence']).first()
        else:
            versioned.licence = \
                Licence.objects.filter(pk=settings.ZDS_APP['content']['default_license_pk']).first()

        if 'introduction' in json:
            versioned.introduction = json['introduction']
        if 'conclusion' in json:
            versioned.conclusion = json['conclusion']

        # then, fill container with children
        fill_containers_from_json(json, versioned)

    else:
        raise Exception('Importation of old version is not yet supported')
        # TODO so here we can support old version !!

    return versioned


def fill_containers_from_json(json_sub, parent):
    """
    Function which call itself to fill container
    :param json_sub: dictionary from "manifest.json"
    :param parent: the container to fill
    """
    # TODO should be static function of `VersionedContent` ?!?
    if 'children' in json_sub:
        for child in json_sub['children']:
            if child['object'] == 'container':
                slug = ''
                try:
                    slug = child['slug']
                except KeyError:
                    pass
                new_container = Container(child['title'], slug)
                if 'introduction' in child:
                    new_container.introduction = child['introduction']
                if 'conclusion' in child:
                    new_container.conclusion = child['conclusion']
                parent.add_container(new_container, generate_slug=(slug != ''))
                if 'children' in child:
                    fill_containers_from_json(child, new_container)
            elif child['object'] == 'extract':
                slug = ''
                try:
                    slug = child['slug']
                except KeyError:
                    pass
                new_extract = Extract(child['title'], slug)
                new_extract.text = child['text']
                parent.add_extract(new_extract, generate_slug=(slug != ''))
            else:
                raise Exception('Unknown object type' + child['object'])


def init_new_repo(db_object, introduction_text, conclusion_text, commit_message=''):
    """
    Create a new repository in `settings.ZDS_APP['contents']['private_repo']` to store the files for a new content.
    Note that `db_object.sha_draft` will be set to the good value
    :param db_object: `PublishableContent` (WARNING: should have a valid `slug`, so previously saved)
    :param introduction_text: introduction from form
    :param conclusion_text: conclusion from form
    :param commit_message : set a commit message instead of the default one
    :return: `VersionedContent` object
    """
    # TODO: should be a static function of an object (I don't know which one yet)

    # create directory
    path = db_object.get_repo_path()
    if not os.path.isdir(path):
        os.makedirs(path, mode=0o777)

    # init repo:
    Repo.init(path, bare=False)
    repo = Repo(path)

    introduction = 'introduction.md'
    conclusion = 'conclusion.md'
    versioned_content = VersionedContent(None,
                                         db_object.type,
                                         db_object.title,
                                         db_object.slug)

    # fill some information that are missing :
    versioned_content.licence = db_object.licence
    versioned_content.description = db_object.description
    versioned_content.introduction = introduction
    versioned_content.conclusion = conclusion

    # fill intro/conclusion:
    f = open(os.path.join(path, introduction), "w")
    f.write(introduction_text.encode('utf-8'))
    f.close()
    f = open(os.path.join(path, conclusion), "w")
    f.write(conclusion_text.encode('utf-8'))
    f.close()

    versioned_content.dump_json()

    # commit change:
    if commit_message == '':
        commit_message = u'Création du contenu'
    repo.index.add(['manifest.json', introduction, conclusion])
    cm = repo.index.commit(commit_message, **get_commit_author())

    # update sha:
    db_object.sha_draft = cm.hexsha
    db_object.sha_beta = None
    db_object.sha_public = None
    db_object.sha_validation = None

    db_object.save()

    versioned_content.current_version = cm.hexsha
    versioned_content.repository = repo

    return versioned_content


def get_commit_author():
    """
    :return: correctly formatted commit author for `repo.index.commit()`
    """
    user = get_current_user()
    aut_user = str(user.pk)
    aut_email = str(user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
    return {'author': Actor(aut_user, aut_email), 'committer': Actor(aut_user, aut_email)}


class PublishableContent(models.Model):
    """
    A tutorial whatever its size or an article.

    A PublishableContent retains metadata about a content in database, such as

    - authors, description, source (if the content comes from another website), subcategory and licence ;
    - Thumbnail and gallery ;
    - Creation, publication and update date ;
    - Public, beta, validation and draft sha, for versioning ;
    - Comment support ;
    - Type, which is either "ARTICLE" or "TUTORIAL"
    """
    class Meta:
        verbose_name = 'Contenu'
        verbose_name_plural = 'Contenus'

    title = models.CharField('Titre', max_length=80)
    slug = models.CharField('Slug', max_length=80)
    description = models.CharField('Description', max_length=200)
    source = models.CharField('Source', max_length=200)
    authors = models.ManyToManyField(User, verbose_name='Auteurs', db_index=True)

    subcategory = models.ManyToManyField(SubCategory,
                                         verbose_name='Sous-Catégorie',
                                         blank=True, null=True, db_index=True)

    # store the thumbnail for tutorial or article
    image = models.ForeignKey(Image,
                              verbose_name='Image du tutoriel',
                              blank=True, null=True,
                              on_delete=models.SET_NULL)

    # every publishable content has its own gallery to manage images
    gallery = models.ForeignKey(Gallery,
                                verbose_name='Galerie d\'images',
                                blank=True, null=True, db_index=True)

    creation_date = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField('Date de publication',
                                   blank=True, null=True, db_index=True)
    update_date = models.DateTimeField('Date de mise à jour',
                                       blank=True, null=True)

    sha_public = models.CharField('Sha1 de la version publique',
                                  blank=True, null=True, max_length=80, db_index=True)
    sha_beta = models.CharField('Sha1 de la version beta publique',
                                blank=True, null=True, max_length=80, db_index=True)
    sha_validation = models.CharField('Sha1 de la version en validation',
                                      blank=True, null=True, max_length=80, db_index=True)
    sha_draft = models.CharField('Sha1 de la version de rédaction',
                                 blank=True, null=True, max_length=80, db_index=True)

    licence = models.ForeignKey(Licence,
                                verbose_name='Licence',
                                blank=True, null=True, db_index=True)
    # as of ZEP 12 this field is no longer the size but the type of content (article/tutorial)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    # zep03 field
    helps = models.ManyToManyField(HelpWriting, verbose_name='Aides', db_index=True)

    relative_images_path = models.CharField(
        'chemin relatif images',
        blank=True,
        null=True,
        max_length=200)

    last_note = models.ForeignKey('ContentReaction', blank=True, null=True,
                                  related_name='last_note',
                                  verbose_name='Derniere note')
    is_locked = models.BooleanField('Est verrouillé', default=False)
    js_support = models.BooleanField('Support du Javascript', default=False)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Rewrite the `save()` function to handle slug uniqueness
        """
        self.slug = uuslug(self.title, instance=self, max_length=80)
        super(PublishableContent, self).save(*args, **kwargs)

    def get_repo_path(self, relative=False):
        """
        Get the path to the tutorial repository
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        if relative:
            return ''
        else:
            # get the full path (with tutorial/article before it)
            return os.path.join(settings.ZDS_APP['content']['repo_private_path'], self.slug)

    def in_beta(self):
        """
        A tutorial is not in beta if sha_beta is `None` or empty
        :return: `True` if the tutorial is in beta, `False` otherwise
        """
        return (self.sha_beta is not None) and (self.sha_beta.strip() != '')

    def in_validation(self):
        """
        A tutorial is not in validation if sha_validation is `None` or empty
        :return: `True` if the tutorial is in validation, `False` otherwise
        """
        return (self.sha_validation is not None) and (self.sha_validation.strip() != '')

    def in_drafting(self):
        """
        A tutorial is not in draft if sha_draft is `None` or empty
        :return: `True` if the tutorial is in draft, `False` otherwise
        """
        return (self.sha_draft is not None) and (self.sha_draft.strip() != '')

    def in_public(self):
        """
        A tutorial is not in on line if sha_public is `None` or empty
        :return: `True` if the tutorial is on line, `False` otherwise
        """
        return (self.sha_public is not None) and (self.sha_public.strip() != '')

    def is_beta(self, sha):
        """
        Is this version of the content the beta version ?
        :param sha: version
        :return: `True` if the tutorial is in beta, `False` otherwise
        """
        return self.in_beta() and sha == self.sha_beta

    def is_validation(self, sha):
        """
        Is this version of the content the validation version ?
        :param sha: version
        :return: `True` if the tutorial is in validation, `False` otherwise
        """
        return self.in_validation() and sha == self.sha_validation

    def is_public(self, sha):
        """
        Is this version of the content the published version ?
        :param sha: version
        :return: `True` if the tutorial is in public, `False` otherwise
        """
        return self.in_public() and sha == self.sha_public

    def is_article(self):
        """
        :return: `True` if article, `False` otherwise
        """
        return self.type == 'ARTICLE'

    def is_tutorial(self):
        """
        :return: `True` if tutorial, `False` otherwise
        """
        return self.type == 'TUTORIAL'

    def load_version_or_404(self, sha=None, public=False):
        """
        Using git, load a specific version of the content. if `sha` is `None`, the draft/public version is used (if
        `public` is `True`).
        :param sha: version
        :param public: if `True`, use `sha_public` instead of `sha_draft` if `sha` is `None`
        :raise Http404: if sha is not None and related version could not be found
        :return: the versioned content
        """
        try:
            return self.load_version(sha, public)
        except BadObject:
            raise Http404

    def load_version(self, sha=None, public=False):
        """
        Using git, load a specific version of the content. if `sha` is `None`, the draft/public version is used (if
        `public` is `True`).
        Note: for practical reason, the returned object is filled with information form DB.
        :param sha: version
        :param public: if `True`, use `sha_public` instead of `sha_draft` if `sha` is `None`
        :raise BadObject: if sha is not None and related version could not be found
        :return: the versioned content
        """
        # load the good manifest.json
        if sha is None:
            if not public:
                sha = self.sha_draft
            else:
                sha = self.sha_public

        path = self.get_repo_path()
        repo = Repo(path)
        data = get_blob(repo.commit(sha).tree, 'manifest.json')
        json = json_reader.loads(data)
        versioned = get_content_from_json(json, sha)
        self.insert_data_in_versioned(versioned)

        return versioned

    def insert_data_in_versioned(self, versioned):
        """
        Insert some additional data from database in a VersionedContent
        :param versioned: the VersionedContent to fill
        """

        attrs = [
            'pk', 'authors', 'authors', 'subcategory', 'image', 'creation_date', 'pubdate', 'update_date', 'source',
            'sha_draft', 'sha_beta', 'sha_validation', 'sha_public'
        ]

        fns = [
            'have_markdown', 'have_html', 'have_pdf', 'have_epub', 'in_beta', 'in_validation', 'in_public',
            'is_article', 'is_tutorial'
        ]

        # load functions and attributs in `versioned`
        for attr in attrs:
            setattr(versioned, attr, getattr(self, attr))
        for fn in fns:
            setattr(versioned, fn, getattr(self, fn)())

        # general information
        versioned.is_beta = self.is_beta(versioned.current_version)
        versioned.is_validation = self.is_validation(versioned.current_version)
        versioned.is_public = self.is_public(versioned.current_version)

    def get_note_count(self):
        """
        :return : umber of notes in the tutorial.
        """
        return ContentReaction.objects.filter(tutorial__pk=self.pk).count()

    def get_last_note(self):
        """
        :return: the last answer in the thread, if any.
        """
        return ContentReaction.objects.all()\
            .filter(tutorial__pk=self.pk)\
            .order_by('-pubdate')\
            .first()

    def first_note(self):
        """
        :return: the first post of a topic, written by topic's author, if any.
        """
        return ContentReaction.objects\
            .filter(tutorial=self)\
            .order_by('pubdate')\
            .first()

    def last_read_note(self):
        """
        :return: the last post the user has read.
        """
        try:
            return ContentRead.objects\
                .select_related()\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note
        except ContentReaction.DoesNotExist:
            return self.first_post()

    def first_unread_note(self):
        """
        :return: Return the first note the user has unread.
        """
        try:
            last_note = ContentRead.objects\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note

            next_note = ContentReaction.objects.filter(
                tutorial__pk=self.pk,
                pubdate__gt=last_note.pubdate)\
                .select_related("author").first()
            return next_note
        except:  # TODO: `except:` is bad.
            return self.first_note()

    def antispam(self, user=None):
        """
        Check if the user is allowed to post in an tutorial according to the SPAM_LIMIT_SECONDS value.
        :param user: the user to check antispam. If `None`, current user is used.
        :return: `True` if the user is not able to note (the elapsed time is not enough), `False` otherwise.
        """
        if user is None:
            user = get_current_user()

        last_user_notes = ContentReaction.objects\
            .filter(tutorial=self)\
            .filter(author=user.pk)\
            .order_by('-position')

        if last_user_notes and last_user_notes[0] == self.last_note:
            last_user_note = last_user_notes[0]
            t = datetime.now() - last_user_note.pubdate
            if t.total_seconds() < settings.ZDS_APP['forum']['spam_limit_seconds']:
                return True
        return False

    def change_type(self, new_type):
        """
        Allow someone to change the content type, basically from tutorial to article
        :param new_type: the new type, either `"ARTICLE"` or `"TUTORIAL"`
        """
        if new_type not in TYPE_CHOICES:
            raise ValueError("This type of content does not exist")
        self.type = new_type

    def have_markdown(self):
        """
        Check if the markdown zip archive is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_repo_path(), self.slug + ".md"))

    def have_html(self):
        """
        Check if the html version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_repo_path(), self.slug + ".html"))

    def have_pdf(self):
        """
        Check if the pdf version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_repo_path(), self.slug + ".pdf"))

    def have_epub(self):
        """
        Check if the standard epub version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_repo_path(), self.slug + ".epub"))

    def repo_delete(self):
        """
        Delete the entities and their filesystem counterparts
        """
        shutil.rmtree(self.get_repo_path(), False)
        Validation.objects.filter(content=self).delete()

        if self.gallery is not None:
            self.gallery.delete()
        if self.in_public():
            shutil.rmtree(self.get_prod_path())


class ContentReaction(Comment):
    """
    A comment written by any user about a PublishableContent he just read.
    """
    class Meta:
        verbose_name = 'note sur un contenu'
        verbose_name_plural = 'notes sur un contenu'

    related_content = models.ForeignKey(PublishableContent, verbose_name='Contenu',
                                        related_name="related_content_note", db_index=True)

    def __unicode__(self):
        return u'<Tutorial pour "{0}", #{1}>'.format(self.related_content, self.pk)

    def get_absolute_url(self):
        """
        :return: the url of the comment
        """
        page = int(ceil(float(self.position) / settings.ZDS_APP['forum']['posts_per_page']))
        return '{0}?page={1}#p{2}'.format(self.related_content.get_absolute_url_online(), page, self.pk)


class ContentRead(models.Model):
    """
    Small model which keeps track of the user viewing tutorials.

    It remembers the PublishableContent he looked and what was the last Note at this time.
    """
    class Meta:
        verbose_name = 'Contenu lu'
        verbose_name_plural = 'Contenu lus'

    content = models.ForeignKey(PublishableContent, db_index=True)
    note = models.ForeignKey(ContentReaction, db_index=True)
    user = models.ForeignKey(User, related_name='content_notes_read', db_index=True)

    def __unicode__(self):
        return u'<Tutoriel "{0}" lu par {1}, #{2}>'.format(self.content, self.user, self.note.pk)


class Validation(models.Model):
    """
    Content validation.
    """
    class Meta:
        verbose_name = 'Validation'
        verbose_name_plural = 'Validations'

    content = models.ForeignKey(PublishableContent, null=True, blank=True,
                                verbose_name='Contenu proposé', db_index=True)
    version = models.CharField('Sha1 de la version',
                               blank=True, null=True, max_length=80, db_index=True)
    date_proposition = models.DateTimeField('Date de proposition', db_index=True)
    comment_authors = models.TextField('Commentaire de l\'auteur')
    validator = models.ForeignKey(User,
                                  verbose_name='Validateur',
                                  related_name='author_content_validations',
                                  blank=True, null=True, db_index=True)
    date_reserve = models.DateTimeField('Date de réservation',
                                        blank=True, null=True)
    date_validation = models.DateTimeField('Date de validation',
                                           blank=True, null=True)
    comment_validator = models.TextField('Commentaire du validateur',
                                         blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING')

    def __unicode__(self):
        return self.content.title

    def is_pending(self):
        """
        Check if the validation is pending
        :return: `True` if status is pending, `False` otherwise
        """
        return self.status == 'PENDING'

    def is_pending_valid(self):
        """
        Check if the validation is pending (but there is a validator)
        :return: `True` if status is pending, `False` otherwise
        """
        return self.status == 'PENDING_V'

    def is_accept(self):
        """
        Check if the content is accepted
        :return: `True` if status is accepted, `False` otherwise
        """
        return self.status == 'ACCEPT'

    def is_reject(self):
        """
        Check if the content is rejected
        :return: `True` if status is rejected, `False` otherwise
        """
        return self.status == 'REJECT'
