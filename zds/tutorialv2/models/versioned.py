import codecs
import contextlib
import copy
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from git import Repo

from zds import json_handler
from zds.tutorialv2.models import CONTENT_TYPES_REQUIRING_VALIDATION
from zds.tutorialv2.models.mixins import TemplatableContentModelMixin
from zds.tutorialv2.utils import InvalidOperationError, default_slug_pool, export_content, get_blob, get_commit_author
from zds.utils.misc import compute_hash
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.uuslug_wrapper import slugify
from zds.utils.validators import InvalidSlugError, check_slug


class Container:
    """
    A container, which can have sub-Containers or Extracts.

    A Container has a title, a introduction and a conclusion, a parent (which can be None) and a position into this
    parent (which is 1 by default).

    It also has a tree depth.

    A container could be either a tutorial/article/opinion, a part or a chapter.
    """

    title = ""
    slug = ""
    introduction = None
    conclusion = None
    parent = None
    ready_to_publish = True  # By default, so that we do not need to migrate "non partial publication ready contents"
    position_in_parent = 1
    children = []
    children_dict = {}
    slug_pool = {}

    def __init__(self, title, slug="", parent=None, position_in_parent=1):
        """Initialize the data model that will handle the dialog with raw versionned data at level container.

        :param title: container title (str)
        :param slug: container slug (basicaly slugify(title))
        :param parent: container parent (None if this container is the root container)
        :param position_in_parent: the display order
        :return:
        """
        self.title = title
        self.slug = slug
        self.parent = parent
        self.position_in_parent = position_in_parent

        self.children = []  # even if you want, do NOT remove this line
        self.children_dict = {}

        self.slug_pool = default_slug_pool()

    def __str__(self):
        return f"<Conteneur '{self.title}'>"

    def __copy__(self):
        cpy = self.__class__(self.title, self.slug, self.parent, self.position_in_parent)
        cpy.children_dict = copy.copy(self.children_dict)
        cpy.children = copy.copy(self.children)
        cpy.slug_pool = copy.deepcopy(self.slug_pool)
        cpy.ready_to_publish = self.ready_to_publish
        cpy.introduction = self.introduction
        cpy.conclusion = self.conclusion
        return cpy

    def get_url_path(self, base_url=""):
        """
        Return the path to the container for use in URLs.
        Preprend with ``base_url`` if specified.
        """
        if self.is_top_container():
            return base_url
        else:
            fragments = []
            current = self
            while current is not None and not current.is_top_container():
                fragments.append(current.slug)
                current = current.parent
            fragments_reversed = reversed(fragments)
            path = f"{'/'.join(fragments_reversed)}/"
            return base_url + path

    def get_list_of_containers(self):
        """
        Return a flat list of containers following the reading order. Extracts are not included.
        Example, if called on the top container: [VersionedContent, Part1, Chapter1, Chapter2, Chapter3, Part2, ...]
        """
        reading_list = [self]
        if not self.has_extracts():
            for child in self.children:
                reading_list.extend(child.get_list_of_containers())
        return reading_list

    def has_extracts(self):
        """Note: This function relies on the fact that every child has the
        same type.

        :return: ``True`` if the container contains extracts, ``False`` otherwise.
        :rtype: bool
        """
        if len(self.children) == 0:
            return False
        return isinstance(self.children[0], Extract)

    def has_sub_containers(self):
        """Note: this function relies on the fact that every child has the
        same type.

        :return: ``True`` if the container contains other containers, ``False`` otherwise.
        :rtype: bool
        """
        if len(self.children) == 0:
            return False
        return isinstance(self.children[0], Container)

    def get_last_child_position(self):
        """
        :return: the position of the last child
        :type: int
        """
        return len(self.children)

    def get_tree_depth(self):
        """Return the depth where this container is found.

        The tree depth of a container is the number of parents of that
        container. It is always lower that 3 because a nested
        container can have at most two parents.

        Keep in mind that extracts can reach a depth of 3 in the
        document tree since there are leaves. Containers are not
        leaves.

        :return: Tree depth
        :rtype: int
        """
        depth = 0
        current = self
        while current.parent is not None:
            current = current.parent
            depth += 1
        return depth

    def get_tree_level(self):
        """Return the level in the tree of this container, i.e the depth of its deepest child.

        :return: tree level
        :rtype: int
        """

        if len(self.children) == 0:
            return 1
        elif isinstance(self.children[0], Extract):
            return 2
        else:
            return 1 + max(i.get_tree_level() for i in self.children)

    def has_child_with_path(self, child_path):
        """Return ``True`` if this container has a child matching the given
        full path.

        :param child_path: the full path (/maincontainer/subc1/subc2/childslug) we want to check
        :return: ``True`` if the child is found, ``False`` otherwise
        :rtype: bool

        """
        if self.get_path(True) not in child_path:
            return False
        return child_path.replace(self.get_path(True), "").replace("/", "") in self.children_dict

    def is_top_container(self) -> bool:
        return self.parent is None

    def top_container(self):
        current = self
        while not current.is_top_container():
            current = current.parent
        return current

    def get_unique_slug(self, title):
        """Generate a slug from the title and check if it is already in slug
        pool. If true, add a "-x" to the end, where "x" is a number
        starting from 1. When generated, it is added to the slug pool.

        Note that the slug cannot be larger than
        ``settings.ZDS_APP['content']['max_slug_size']``, due to maximum
        file size limitation.

        :param title: title from which the slug is generated (with ``slugify()``)
        :return: the unique slug
        :rtype: str
        """
        base = slugify(title)

        if not check_slug(base):
            raise InvalidSlugError(base, source=title)

        max_slug_size = settings.ZDS_APP["content"]["maximum_slug_size"]

        # Slugs may look like `some-article-title-1234`.
        max_suffix_digit_count = 4

        if len(base) > max_slug_size - 1 - max_suffix_digit_count:
            # There is a `- 1` because of the dash between the slug
            # itself and the numeric suffix.
            base = base[:max_slug_size] - 1 - max_suffix_digit_count

        if base not in self.slug_pool:
            self.slug_pool[base] = 1
            return base

        n = self.slug_pool[base]
        while True:
            new_slug = base + "-" + str(n)
            self.slug_pool[base] += 1
            if new_slug not in self.slug_pool:
                self.slug_pool[new_slug] = 1
                return new_slug
            n = self.slug_pool[base]

    def __add_slug_to_pool(self, slug):
        """Add a slug to the slug pool to be taken into account when
        generating a unique slug.

        :param slug: the slug to add
        :raise InvalidOperationErrpr: if the slug already exists

        """
        if slug in self.slug_pool:
            raise InvalidOperationError(
                _("Le slug « {} » est déjà présent dans le conteneur « {} »").format(slug, self.title)
            )
        self.slug_pool[slug] = 1

    def long_slug(self):
        """
        :return: a long slug which embeds parent slugs
        :rtype: str
        """
        long_slug = ""
        if self.parent:
            long_slug = self.parent.long_slug() + "__"
        return long_slug + self.slug

    def can_add_container(self) -> bool:
        """
        Return `True` if adding child containers is allowed.
        Adding subcontainers is forbidden:
        * if the container already has extracts as children,
        * or if the limit of nested containers has been reached.
        """
        return not self.has_extracts() and self.get_tree_depth() < settings.ZDS_APP["content"]["max_tree_depth"] - 1

    def can_add_extract(self):
        """Return ``True`` if this container can contain extracts, i.e doesn't
        contain any container (only zero or more extracts) and is not
        too deeply nested.

        :return: ``True`` if this container accept child extract, ``False`` otherwise
        :rtype: bool
        """
        if not self.has_sub_containers():
            if self.get_tree_depth() <= settings.ZDS_APP["content"]["max_tree_depth"]:
                return True
        return False

    def add_container(self, container, generate_slug=False):
        """Add a child Container, but only if no extract were previously added
        and tree depth is lower than 2.

        .. attention::

            This function will raise an Exception if the publication
            is an article

        :param container: the new container
        :param generate_slug: if ``True``, asks the top container a unique slug for this object
        :raises InvalidOperationError: if the new container cannot be added. Please use\
        ``can_add_container`` first to make sure you can use ``add_container``.
        """
        if self.can_add_container():
            if generate_slug:
                container.slug = self.get_unique_slug(container.title)
            else:
                self.__add_slug_to_pool(container.slug)
            container.parent = self
            container.position_in_parent = self.get_last_child_position() + 1
            self.children.append(container)
            self.children_dict[container.slug] = container
        else:
            raise InvalidOperationError(_("Impossible d'ajouter un conteneur au conteneur « {} »").format(self.title))

    def add_extract(self, extract, generate_slug=False):
        """Add a child container, but only if no container were previously added

        :param extract: the new extract
        :param generate_slug: if ``True``, ask the top container a unique slug for this object
        :raise InvalidOperationError: if the extract can't be added to this container.
        """
        if self.can_add_extract():
            if generate_slug:
                extract.slug = self.get_unique_slug(extract.title)
            else:
                self.__add_slug_to_pool(extract.slug)
            extract.container = self
            extract.position_in_parent = self.get_last_child_position() + 1
            self.children.append(extract)
            self.children_dict[extract.slug] = extract
        else:
            raise InvalidOperationError(_("Impossible d'ajouter un extrait au conteneur « {} »").format(self.title))

    def update_children(self):
        """Update the path for introduction and conclusion for the container and all its children. If the children is an
        extract, update the path to the text instead. This function is useful when ``self.slug`` has
        changed.

        Note: this function does not account for a different arrangement of the files.
        """
        # TODO : path comparison instead of pure rewritring ?
        self.introduction = os.path.join(self.get_path(relative=True), "introduction.md")
        self.conclusion = os.path.join(self.get_path(relative=True), "conclusion.md")
        for child in self.children:
            if isinstance(child, Container):
                child.update_children()
            elif isinstance(child, Extract):
                child.text = child.get_path(relative=True)

    def get_path(self, relative=False, os_sensitive=True):
        """Get the physical path to the draft version of the container.
        Note: this function rely on the fact that the top container is VersionedContainer.

        :param relative: if ``True``, the path will be relative, absolute otherwise.
        :type relative: bool
        :param os_sensitive: if ``True`` will use os.path.join to ensure compatibility with all OS, otherwise \\
                             will build with ``/``, mainly for urls.
        :return: physical path
        :rtype: str
        """
        base = ""
        if self.parent:
            base = self.parent.get_path(relative=relative)
        return os.path.join(base, self.slug) if os_sensitive else "/".join([base, self.slug]).strip("/")

    def get_prod_path(self, relative=False, file_ext="html"):
        """Get the physical path to the public version of the container. If the container have extracts, then it\
        returns the final HTML file.

        :param file_ext: the dumped file extension
        :return:
        :param relative: return a relative path instead of an absolute one
        :type relative: bool
        :return: physical path
        :rtype: str
        """
        base = ""
        if self.parent:
            base = self.parent.get_prod_path(relative=relative)
        path = os.path.join(base, self.slug)

        if self.has_extracts():
            path += "." + file_ext

        return path

    def get_absolute_url(self):
        """
        :return: url to access the container
        :rtype: str
        """
        return self.top_container().get_absolute_url() + self.get_path(relative=True, os_sensitive=False) + "/"

    def get_absolute_url_online(self):
        """

        :return: the 'online version' of the url
        :rtype: str
        """
        base = ""

        if self.parent:
            base = self.parent.get_absolute_url_online()

        base += self.slug + "/"

        return base

    def get_absolute_url_beta(self):
        """
        :return: url to access the container in beta
        :rtype: str
        """

        if self.top_container().sha_beta is not None:
            base = ""
            if self.parent:
                base = self.parent.get_absolute_url_beta()

            return base + self.slug + "/"
        else:
            return self.get_absolute_url()

    def get_edit_url(self):
        """
        :return: url to edit the container
        :rtype: str
        """
        slugs = [self.slug]
        parent = self.parent
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.top_container().pk]
        args.extend(slugs)

        return reverse("content:edit-container", args=args)

    def get_delete_url(self):
        """
        :return: url to edit the container
        :rtype: str
        """
        slugs = [self.slug]
        parent = self.parent
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.top_container().pk]
        args.extend(slugs)

        return reverse("content:delete", args=args)

    def get_introduction(self):
        """
        :return: the introduction from the file in ``self.introduction``
        :rtype: str
        """
        if self.introduction:
            return (
                get_blob(
                    self.top_container().repository.commit(self.top_container().current_version).tree,
                    self.introduction.replace("\\", "/"),
                )
                or ""
            )
        return ""

    def get_conclusion(self):
        """
        :return: the conclusion from the file in ``self.conclusion``
        :rtype: str
        """
        if self.conclusion:
            return (
                get_blob(
                    self.top_container().repository.commit(self.top_container().current_version).tree,
                    self.conclusion.replace("\\", "/"),
                )
                or ""
            )
        return ""

    def get_introduction_online(self):
        """The introduction content for online version.

        This method should be only used in templates

        :return: the full text if introduction exists, empty string otherwise
        :rtype: str
        """
        if self.introduction:
            path = os.path.join(self.top_container().get_prod_path(), self.introduction)
            if os.path.isfile(path):
                return codecs.open(path, "r", encoding="utf-8").read()
        return ""

    def get_conclusion_online(self):
        """The conclusion content for online version.

        This method should be only used in templates

        :return: the full text if introduction exists, empty string otherwise
        :rtype: str
        """
        if self.conclusion:
            path = os.path.join(self.top_container().get_prod_path(), self.conclusion)
            if os.path.isfile(path):
                return codecs.open(path, "r", encoding="utf-8").read()
        return ""

    def get_content_online(self):
        if os.path.isfile(self.get_prod_path()):
            return codecs.open(self.get_prod_path(), "r", encoding="utf-8").read()

    def compute_hash(self):
        """Compute an MD5 hash from the introduction and conclusion, for comparison purpose

        :return: MD5 hash
        :rtype: str
        """

        files = []
        if self.introduction:
            files.append(os.path.join(self.top_container().get_path(), self.introduction))
        if self.conclusion:
            files.append(os.path.join(self.top_container().get_path(), self.conclusion))

        return compute_hash(files)

    def repo_update(self, title, introduction, conclusion, commit_message="", do_commit=True, update_slug=True):
        """Update the container information and commit them into the repository

        :param title: the new title
        :param introduction: the new introduction text
        :param conclusion: the new conclusion text
        :param commit_message: commit message that will be used instead of the default one
        :param do_commit: perform the commit in repository if ``True``
        :return: commit sha
        :rtype: str
        """

        if title is None:
            raise PermissionDenied

        repo = self.top_container().repository

        # update title
        if title != self.title:
            self.title = title
            if self.get_tree_depth() > 0:  # if top container, slug is generated from DB, so already changed
                old_path = self.get_path(relative=True)
                old_slug = self.slug

                # move things
                if update_slug:
                    self.slug = self.parent.get_unique_slug(title)
                    new_path = self.get_path(relative=True)
                    repo.index.move([old_path, new_path])

                # update manifest
                self.update_children()

                # update parent children dict:
                self.parent.children_dict.pop(old_slug)
                self.parent.children_dict[self.slug] = self

        # update introduction and conclusion (if any)
        path = self.top_container().get_path()
        rel_path = self.get_path(relative=True)

        if introduction is not None:
            if self.introduction is None:
                self.introduction = os.path.join(rel_path, "introduction.md")

            f = codecs.open(os.path.join(path, self.introduction), "w", encoding="utf-8")
            f.write(introduction)
            f.close()
            repo.index.add([self.introduction])

        elif self.introduction:
            repo.index.remove([self.introduction])
            os.remove(os.path.join(path, self.introduction))
            self.introduction = None

        if conclusion is not None:
            if self.conclusion is None:
                self.conclusion = os.path.join(rel_path, "conclusion.md")

            f = codecs.open(os.path.join(path, self.conclusion), "w", encoding="utf-8")
            f.write(conclusion)
            f.close()
            repo.index.add([self.conclusion])

        elif self.conclusion:
            repo.index.remove([self.conclusion])
            os.remove(os.path.join(path, self.conclusion))
            self.conclusion = None

        self.top_container().dump_json()
        repo.index.add(["manifest.json"])

        if not commit_message:
            commit_message = _("Mise à jour de « {} »").format(self.title)

        if do_commit:
            return self.top_container().commit_changes(commit_message)

    def repo_add_container(
        self, title, introduction, conclusion, commit_message="", do_commit=True, slug=None, ready_to_publish=None
    ):
        """
        :param title: title of the new container
        :param introduction: text of its introduction
        :param conclusion: text of its conclusion
        :param commit_message: commit message that will be used instead of the default one
        :param do_commit: perform the commit in repository if ``True``
        :return: commit sha
        :rtype: str
        """
        if slug is None:
            subcontainer = Container(title)
        else:
            subcontainer = Container(title, slug=slug)
        # can a subcontainer be added ?
        try:
            self.add_container(subcontainer, generate_slug=slug is None)
        except InvalidOperationError:
            raise PermissionDenied

        # create directory
        repo = self.top_container().repository
        path = self.top_container().get_path()
        rel_path = subcontainer.get_path(relative=True)
        with contextlib.suppress(FileExistsError):
            Path(path, rel_path).mkdir(parents=True)

        repo.index.add([rel_path])

        # make it
        if not commit_message:
            commit_message = _("Création du conteneur « {} »").format(title)

        if ready_to_publish is not None:
            subcontainer.ready_to_publish = ready_to_publish
        return subcontainer.repo_update(
            title, introduction, conclusion, commit_message=commit_message, do_commit=do_commit
        )

    def repo_add_extract(self, title, text, commit_message="", do_commit=True, slug=None):
        """
        :param title: title of the new extract
        :param text: text of the new extract
        :param commit_message: commit message that will be used instead of the default one
        :param do_commit: perform the commit in repository if ``True``
        :param generate_slug: indicates that is must generate slug
        :return: commit sha
        :rtype: str
        """
        if not slug:
            extract = Extract(title)
        else:
            extract = Extract(title, slug)
        # can an extract be added ?
        try:
            self.add_extract(extract, generate_slug=slug is None)
        except InvalidOperationError:
            raise PermissionDenied

        # make it
        if not commit_message:
            commit_message = _("Création de l'extrait « {} »").format(title)

        return extract.repo_update(title, text, commit_message=commit_message, do_commit=do_commit)

    def repo_delete(self, commit_message="", do_commit=True):
        """
        :param commit_message: commit message used instead of default one if provided
        :param do_commit: tells if we have to commit the change now or let the outer program do it
        :return: commit sha
        :rtype: str
        """
        path = self.get_path(relative=True)
        repo = self.top_container().repository
        repo.index.remove([path], r=True)
        shutil.rmtree(self.get_path())  # looks like removing from git is not enough!!

        # now, remove from manifest
        # work only if slug is correct
        top = self.parent
        top.children_dict.pop(self.slug)
        top.children.pop(top.children.index(self))

        # commit
        top.top_container().dump_json()
        repo.index.add(["manifest.json"])

        if not commit_message:
            commit_message = _("Suppression du conteneur « {} »").format(self.title)

        if do_commit:
            return self.top_container().commit_changes(commit_message)

    def move_child_up(self, child_slug):
        """Change the child's ordering by moving up the child whose slug equals child_slug.
        This method **does not** automaticaly update the repo.

        :param child_slug: the child's slug
        :raise ValueError: if the slug does not refer to an existing child
        :raise IndexError: if the extract is already the first child
        """
        if child_slug not in self.children_dict:
            raise ValueError(_(child_slug + " n'existe pas."))
        child_pos = self.children.index(self.children_dict[child_slug])
        if child_pos == 0:
            raise IndexError(_(child_slug + " est le premier élément."))
        self.children[child_pos], self.children[child_pos - 1] = self.children[child_pos - 1], self.children[child_pos]
        self.children[child_pos].position_in_parent = child_pos + 1
        self.children[child_pos - 1].position_in_parent = child_pos

    def move_child_down(self, child_slug):
        """Change the child's ordering by moving down the child whose slug equals child_slug.
        This method **does not** automaticaly update the repo.

        :param child_slug: the child's slug
        :raise ValueError: if the slug does not refer to an existing child
        :raise IndexError: if the extract is already the last child
        """
        if child_slug not in self.children_dict:
            raise ValueError(_(child_slug + " n'existe pas."))
        child_pos = self.children.index(self.children_dict[child_slug])
        if child_pos == len(self.children) - 1:
            raise IndexError(_(child_slug + " est le dernier élément."))
        self.children[child_pos], self.children[child_pos + 1] = self.children[child_pos + 1], self.children[child_pos]
        self.children[child_pos].position_in_parent = child_pos
        self.children[child_pos + 1].position_in_parent = child_pos + 1

    def move_child_after(self, child_slug, refer_slug):
        """Change the child's ordering by moving the child to be below the reference child.
        This method **does not** automaticaly update the repo

        :param child_slug: the child's slug
        :param refer_slug: the referent child's slug.
        :raise ValueError: if one slug does not refer to an existing child
        """
        if child_slug not in self.children_dict:
            raise ValueError(_(child_slug + " n'existe pas."))
        if refer_slug not in self.children_dict:
            raise ValueError(_(refer_slug + " n'existe pas."))
        child_pos = self.children.index(self.children_dict[child_slug])
        refer_pos = self.children.index(self.children_dict[refer_slug])

        # if we want our child to get down (reference is an lower child)
        if child_pos < refer_pos:
            for i in range(child_pos, refer_pos):
                self.move_child_down(child_slug)
        elif child_pos > refer_pos:
            # if we want our child to get up (reference is an upper child)
            for i in range(child_pos, refer_pos + 1, -1):
                self.move_child_up(child_slug)

    def move_child_before(self, child_slug, refer_slug):
        """Change the child's ordering by moving the child to be just above the reference child.
        This method **does not** automaticaly update the repo.

        :param child_slug: the child's slug
        :param refer_slug: the referent child's slug.
        :raise ValueError: if one slug does not refer to an existing child
        """
        if child_slug not in self.children_dict:
            raise ValueError(_(child_slug + " n'existe pas."))
        if refer_slug not in self.children_dict:
            raise ValueError(_(refer_slug + " n'existe pas."))
        child_pos = self.children.index(self.children_dict[child_slug])
        refer_pos = self.children.index(self.children_dict[refer_slug])

        # if we want our child to get down (reference is an lower child)
        if child_pos < refer_pos:
            for i in range(child_pos, refer_pos - 1):
                self.move_child_down(child_slug)
        elif child_pos > refer_pos:
            # if we want our child to get up (reference is an upper child)
            for i in range(child_pos, refer_pos, -1):
                self.move_child_up(child_slug)

    def traverse(self, only_container=True):
        """Traverse the container.

        :param only_container: if we only want container's paths, not extract
        :return: a generator that traverse all the container recursively (depth traversal)
        :rtype: collections.Iterable[Container|Extract]
        """
        yield self
        for child in self.children:
            if isinstance(child, Container):
                yield from child.traverse(only_container)
            elif not only_container:
                yield child

    def get_level_as_string(self):
        """Get a word (Part/Chapter/Section) for the container level

        .. attention::

            this deals with internationalized string

        :return: The string representation of this level
        :rtype: str
        """
        if self.get_tree_depth() == 0:
            return self.type
        elif self.get_tree_depth() == 1:
            return _("Partie")
        elif self.get_tree_depth() == 2:
            return _("Chapitre")
        return _("Sous-chapitre")

    def get_next_level_as_string(self):
        """Same as ``self.get_level_as_string()`` but try to guess the level of this container's children

        :return: The string representation of next level (upper)
        :rtype: str
        """
        if self.get_tree_depth() == 0 and self.can_add_container():
            return _("Partie")
        elif self.get_tree_depth() == 1 and self.can_add_container():
            return _("Chapitre")
        else:
            return _("Section")

    def is_chapter(self):
        """
        Check if the container level is Chapter

        :return: True if the container level is Chapter
        :rtype: bool
        """
        if self.get_tree_depth() == 2:
            return True
        return False

    def next_level_is_chapter(self):
        """Same as ``self.is_chapter()`` but check the container's children

        :return: True if the container next level is Chapter
        :rtype: bool
        """
        if self.get_tree_depth() == 1 and self.can_add_container():
            return True
        return False

    def remove_children(self, children_slugs):
        for slug in children_slugs:
            if slug not in self.children_dict:
                continue
            to_be_remove = self.children_dict[slug]
            self.children.remove(to_be_remove)
            del self.children_dict[slug]

    def _dump_html(self, file_path, content, db_object):
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(emarkdown(content, db_object.js_support))
        except (UnicodeError, UnicodeEncodeError):
            from zds.tutorialv2.publication_utils import FailureDuringPublication

            raise FailureDuringPublication(
                _(
                    "Une erreur est survenue durant la publication de l'introduction de « {} »,"
                    " vérifiez le code markdown"
                ).format(self.title)
            )

    def publish_introduction_and_conclusion(self, base_dir, db_object):
        if self.has_extracts():
            return
        current_dir_path = Path(base_dir, self.get_prod_path(relative=True))  # create subdirectory
        with contextlib.suppress(FileExistsError):
            current_dir_path.mkdir(parents=True)

        if self.introduction:
            path = current_dir_path / "introduction.html"
            self._dump_html(path, self.get_introduction(), db_object)
            self.introduction = Path(self.get_path(relative=True), "introduction.html")

        if self.conclusion:
            path = current_dir_path / "conclusion.html"
            self._dump_html(path, self.get_conclusion(), db_object)
            self.conclusion = Path(self.get_path(relative=True), "conclusion.html")

    def publish_extracts(self, base_dir, is_js, template, failure_exception):
        """
        Publish the current element thanks to a templated view.

        :param base_dir: directory into which we will put the result
        :param is_js: jsfiddle activation flag
        :param template: templated view name
        :param failure_exception: the exception to throw when we fail
        :return:
        """
        parsed = render_to_string(template, {"container": self, "is_js": is_js})
        with Path(base_dir, self.get_prod_path(relative=True)).open("w", encoding="utf-8") as f:
            try:
                f.write(parsed)
            except (UnicodeError, UnicodeEncodeError):
                raise failure_exception(
                    _("Une erreur est survenue durant la publication de « {} »," " vérifiez le code markdown").format(
                        self.title
                    )
                )
        # as introduction and conclusion are published in the full file, we remove reference to them
        self.introduction = None
        self.conclusion = None

    def is_validable(self):
        """Return ``True`` if the container would be in the public version if the content is validated."""
        if self.parent is not None and not self.parent.is_validable():
            return False
        return self.ready_to_publish


class Extract:
    """
    A content extract from a Container.

    It has a title, a position in the parent container and a text.
    """

    title = ""
    slug = ""
    container = None
    position_in_parent = 1
    text = None

    def __init__(self, title, slug="", container=None, position_in_parent=1):
        self.title = title
        self.slug = slug
        self.container = container
        self.position_in_parent = position_in_parent

    def __str__(self):
        return f"<Extrait '{self.title}'>"

    def get_url_path(self, base_url=""):
        return f"{base_url}{self.container.get_url_path()}#{self.position_in_parent}-{self.slug}"

    def get_absolute_url(self):
        """Find the url that point to the offline version of this extract

        :return: the url to access the tutorial offline
        :rtype: str
        """
        return f"{self.container.get_absolute_url()}#{self.position_in_parent}-{self.slug}"

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        :rtype: str
        """
        return f"{self.container.get_absolute_url_online()}#{self.position_in_parent}-{self.slug}"

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        :rtype: str
        """
        return f"{self.container.get_absolute_url_beta()}#{self.position_in_parent}-{self.slug}"

    def get_edit_url(self):
        """
        :return: url to edit the extract
        :rtype: str
        """
        slugs = [self.slug]
        parent = self.container
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.container.top_container().pk]
        args.extend(slugs)

        return reverse("content:edit-extract", args=args)

    def get_full_slug(self):
        """Get the slug of curent extract with its full path (part1/chapter1/slug_of_extract).

        This method is an alias to ``extract.get_path(True)[:-3]``
        (removes the ``.md`` file extension).

        :rtype: str

        """
        return self.get_path(True)[:-3]

    def get_first_level_slug(self):
        """
        :return: the ``first_level_slug``, if (and only if) the parent container is a chapter
        :rtype: str
        """
        if self.container.get_tree_depth() == 2:
            return self.container.parent.slug

        return ""

    def get_delete_url(self):
        """
        :return: URL to delete the extract
        :rtype: str
        """
        slugs = [self.slug]
        parent = self.container
        while parent is not None:
            slugs.append(parent.slug)
            parent = parent.parent
        slugs.reverse()
        args = [self.container.top_container().pk]
        args.extend(slugs)

        return reverse("content:delete", args=args)

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the extract.
        :param relative: if ``True``, the path will be relative, absolute otherwise.
        :return: physical path
        :rtype: str
        """
        return os.path.join(self.container.get_path(relative=relative), self.slug) + ".md"

    def get_text(self):
        """
        :return: versioned text
        :rtype: str
        """
        if self.text:
            return get_blob(
                self.container.top_container().repository.commit(self.container.top_container().current_version).tree,
                self.text.replace("\\", "/"),
            )
        return ""

    def compute_hash(self):
        """Compute an MD5 hash from the text, for comparison purpose

        :return: MD5 hash of the text
        :rtype: str
        """

        if self.text:
            return compute_hash([self.get_path()])

        else:
            return compute_hash([])

    def repo_update(self, title, text, commit_message="", do_commit=True):
        """
        :param title: new title of the extract
        :param text: new text of the extract
        :param commit_message: commit message that will be used instead of the default one
        :return: commit sha
        :rtype: str
        """

        if title is None:
            raise PermissionDenied

        repo = self.container.top_container().repository

        if title != self.title:
            # get a new slug
            old_path = self.get_path(relative=True)
            old_slug = self.slug
            self.title = title
            self.slug = self.container.get_unique_slug(title)

            # move file
            new_path = self.get_path(relative=True)
            repo.index.move([old_path, new_path])

            # update parent children dict:
            self.container.children_dict.pop(old_slug)
            self.container.children_dict[self.slug] = self

        # edit text
        path = self.container.top_container().get_path()

        if text is not None:
            self.text = self.get_path(relative=True)
            f = codecs.open(os.path.join(path, self.text), "w", encoding="utf-8")
            f.write(text)
            f.close()

            repo.index.add([self.text])

        elif self.text:
            if os.path.exists(os.path.join(path, self.text)):
                repo.index.remove([self.text])
                os.remove(os.path.join(path, self.text))

            self.text = None

        # make it
        self.container.top_container().dump_json()
        repo.index.add(["manifest.json"])

        if not commit_message:
            commit_message = _("Modification de l'extrait « {} », situé dans le conteneur « {} »").format(
                self.title, self.container.title
            )

        if do_commit:
            return self.container.top_container().commit_changes(commit_message)

    def repo_delete(self, commit_message="", do_commit=True):
        """
        :param commit_message: commit message used instead of default one if provided
        :param do_commit: tells if we have to commit the change now or let the outer program do it
        :return: commit sha, None if no commit is done
        :rtype: str
        """
        path = self.text
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
        repo.index.add(["manifest.json"])

        if not commit_message:
            commit_message = _("Suppression de l'extrait « {} »").format(self.title)

        if do_commit:
            return self.container.top_container().commit_changes(commit_message)

    def get_tree_depth(self):
        """Return the depth where this extract is found.

        The tree depth of an extract is the number of parents of that
        extract. It is always lower that 4 because an extract can have
        at most three parents.

        Keep in mind that containers can't reach a depth of 3 in the
        document tree since there are not leaves.

        :return: Tree depth
        :rtype: int
        """
        depth = 1
        current = self.container
        while current.parent is not None:
            current = current.parent
            depth += 1
        return depth

    def is_validable(self):
        return self.container.is_validable()


class VersionedContent(Container, TemplatableContentModelMixin):
    """
    This class is used to handle a specific version of a content.

    It is created from the 'manifest.json' file, and could dump information in it.

    For simplicity, it also contains read-only DB information filled at the creation.
    """

    current_version = None
    slug_repository = ""
    repository = None

    PUBLIC = False  # this variable is set to true when the VersionedContent is created from the public repository

    # Metadata from json :
    description = ""
    type = ""
    licence = None

    # Metadata from DB :
    pk = 0
    sha_draft = None
    sha_beta = None
    sha_public = None
    sha_validation = None
    sha_picked = None
    is_beta = False
    is_validation = False
    is_public = False
    in_beta = False
    in_validation = False
    in_public = False

    authors = None
    subcategory = None
    image = None
    creation_date = None
    pubdate = None
    update_date = None
    source = None
    antispam = True
    tags = None
    converted_to = None
    content_type_attribute = "type"

    def __copy__(self):
        cpy = self.__class__(self.current_version, self.type, self.title, self.slug, self.slug_repository)
        cpy.children_dict = copy.copy(self.children_dict)
        cpy.children = copy.copy(self.children)
        cpy.slug_pool = copy.deepcopy(self.slug_pool)
        cpy.ready_to_publish = self.ready_to_publish
        cpy.introduction = self.introduction
        cpy.conclusion = self.conclusion
        for attr in dir(cpy):
            value = getattr(cpy, attr)
            if not value and not callable(value):
                setattr(cpy, attr, getattr(self, attr))
        return cpy

    def __init__(self, current_version, _type, title, slug, slug_repository=""):
        """
        :param current_version: version of the content
        :param _type: either "TUTORIAL", "ARTICLE" or "OPINION"
        :param title: title of the content
        :param slug: slug of the content
        :param slug_repository: slug of the directory that contains the repository, named after database slug.
            if not provided, use ``self.slug`` instead.
        """

        Container.__init__(self, title, slug)
        self.current_version = current_version
        self.type = _type

        if slug_repository != "":
            self.slug_repository = slug_repository
        else:
            self.slug_repository = slug

        if self.slug != "" and os.path.exists(self.get_path()):
            self.repository = Repo(self.get_path())

    def __str__(self):
        return self.title

    def requires_validation(self) -> bool:
        return self.type in CONTENT_TYPES_REQUIRING_VALIDATION

    def get_absolute_url(self, version=None):
        return TemplatableContentModelMixin.get_absolute_url(self, version)

    def textual_type(self):
        """Create a internationalized string with the human readable type of this content e.g “The Article”

        :return: internationalized string
        :rtype: str
        """
        if self.is_article:
            return _("L’Article")
        elif self.is_tutorial:
            return _("Le Tutoriel")
        elif self.is_opinion:
            return _("Le Billet")
        else:
            return _("Le Contenu")

    def get_absolute_url_online(self):
        """

        :return: the url to access the content when online
        :rtype: str
        """
        _reversed = ""

        if self.is_article:
            _reversed = "article"
        elif self.is_tutorial:
            _reversed = "tutorial"
        elif self.is_opinion:
            _reversed = "opinion"
        return reverse(_reversed + ":view", kwargs={"pk": self.pk, "slug": self.slug})

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        :rtype: str
        """
        if self.in_beta:
            return reverse("content:beta-view", args=[self.pk, self.slug])
        else:
            return self.get_absolute_url()

    def get_path(self, relative=False, use_current_slug=False):
        """Get the physical path to the draft version of the Content.

        :param relative: if ``True``, the path will be relative, absolute otherwise.
        :param use_current_slug: if ``True``, use ``self.slug`` instead of ``self.slug_last_draft``
        :return: physical path
        :rtype: str
        """
        if relative:
            return ""
        else:
            slug = self.slug_repository
            if use_current_slug:
                slug = self.slug
            return os.path.join(settings.ZDS_APP["content"]["repo_private_path"], slug)

    def get_prod_path(self, relative=False, file_ext="html"):
        """Get the physical path to the public version of the content. If it
        has one or more extracts (if it is a mini-tutorial or an
        article), return the path of the HTML file.

        :param relative: return the relative path instead of the absolute one
        :return: physical path
        :rtype: str

        """
        path = ""

        if not relative:
            path = os.path.join(settings.ZDS_APP["content"]["repo_public_path"], self.slug)

        if self.has_extracts():
            path = os.path.join(path, self.slug + "." + file_ext)

        return path

    def get_list_of_chapters(self) -> list[Container]:
        continuous_list = []
        if len(self.children) != 0 and isinstance(self.children[0], Container):  # children must be Containers!
            for child in self.children:
                if len(child.children) != 0:
                    if isinstance(child.children[0], Extract):
                        continuous_list.append(child)  # it contains Extract, this is a chapter, so paginated
                    else:  # Container is a part
                        for sub_child in child.children:
                            continuous_list.append(sub_child)  # even if `sub_child.children` is empty, it's a chapter
        return continuous_list

    def get_json(self):
        """
        :return: raw JSON file
        :rtype: str
        """
        dct = export_content(self)
        data = json_handler.dumps(dct, indent=4, ensure_ascii=False)
        return data

    def dump_json(self, path=None):
        """Write the JSON into file

        :param path: path to the file. If ``None``, write in 'manifest.json'
        """
        if path is None:
            man_path = os.path.join(self.get_path(), "manifest.json")
        else:
            man_path = path
        json_data = codecs.open(man_path, "w", encoding="utf-8")
        json_data.write(self.get_json())
        json_data.close()

    def repo_update_top_container(self, title, slug, introduction, conclusion, commit_message="", do_commit=True):
        """Update the top container information and commit them into the repository.
        Note that this is slightly different from the ``repo_update()`` function, because slug is generated using DB

        :param title: the new title
        :param slug: the new slug, according to title (choose using DB!!)
        :param introduction: the new introduction text
        :param conclusion: the new conclusion text
        :param commit_message: commit message that will be used instead of the default one
        :param do_commit: if ``True``, also commit change
        :return: commit sha
        :rtype: str
        """

        if slug != self.slug:
            # move repository
            old_path = self.get_path(use_current_slug=True)
            self.slug = slug
            new_path = self.get_path(use_current_slug=True)
            shutil.move(old_path, new_path)
            self.repository = Repo(new_path)
            self.slug_repository = slug

        return self.repo_update(title, introduction, conclusion, commit_message=commit_message, do_commit=do_commit)

    def commit_changes(self, commit_message):
        """Commit change made to the repository

        :param commit_message: The message that will appear in content history
        :return: commit sha
        :rtype: str
        """
        cm = self.repository.index.commit(commit_message, **get_commit_author())

        self.sha_draft = cm.hexsha
        self.current_version = cm.hexsha

        return cm.hexsha

    def change_child_directory(self, child, adoptive_parent):
        """Move an element of this content to a new location.
        This method changes the repository index and stage every change but does **not** commit.

        :param child: the child we want to move, can be either an Extract or a Container object
        :param adoptive_parent: the container where the child *will be* moved, must be a Container object
        """

        old_path = child.get_path(False)  # absolute path because we want to access the address
        if isinstance(child, Extract):
            old_parent = child.container
            old_parent.children = [c for c in old_parent.children if c.slug != child.slug]
            adoptive_parent.add_extract(child, True)
        else:
            old_parent = child.parent
            old_parent.children = [c for c in old_parent.children if c.slug != child.slug]
            adoptive_parent.add_container(child, True)
        self.repository.index.move([old_path, child.get_path(False)])
        old_parent.update_children()
        adoptive_parent.update_children()
        self.dump_json()


class PublicContent(VersionedContent):
    """This is the public version of a VersionedContent, created from public repository"""

    def __init__(self, current_version, _type, title, slug):
        """This initialisation function avoid the loading of the Git repository

        :param current_version: version of the content
        :param _type: either "TUTORIAL", "ARTICLE" or "OPINION"
        :param title: title of the content
        :param slug: slug of the content
        """

        super().__init__(current_version, _type, title, slug)
        self.PUBLIC = True


class NotAPublicVersion(Exception):
    """Exception raised when a given version is not a public version as it should be"""
