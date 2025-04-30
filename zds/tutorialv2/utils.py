import logging
import os
from collections import OrderedDict, namedtuple
from urllib.parse import quote, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from git import Actor, Repo

from zds.tutorialv2 import signals
from zds.tutorialv2.models import CONTENT_TYPE_LIST
from zds.utils import get_current_user
from zds.utils.models import Licence
from zds.utils.validators import InvalidSlugError, check_slug, slugify_raise_on_invalid

logger = logging.getLogger(__name__)


def all_is_string_appart_from_given_keys(dict_representation, keys=("children",)):
    """check all keys are string appart from the children key
    :param dict_representation: the json decoded dictionary
    :param keys: keys that do not need to be string
    :type dict_representation: dict
    :return:
    :rtype: bool
    """
    return all([isinstance(value, str) for key, value in list(dict_representation.items()) if key not in keys])


def search_container_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` keys\
    or the string representation
    :return: the Container object we were searching for
    :rtype: zds.tutorialv2.models.versioned.Container
    :raise Http404: if no suitable container is found
    """

    from zds.tutorialv2.models.versioned import Container

    if isinstance(kwargs_array, str):
        dic = {}
        dic["parent_container_slug"] = kwargs_array.split("/")[0]
        if len(kwargs_array.split("/")) >= 2:
            dic["container_slug"] = kwargs_array.split("/")[1]
        kwargs_array = dic

    if "parent_container_slug" in kwargs_array:
        try:
            container = base_content.children_dict[kwargs_array["parent_container_slug"]]
        except KeyError:
            raise Http404("Aucun conteneur trouvé.")
        else:
            if not isinstance(container, Container):
                raise Http404("Aucun conteneur trouvé.")
    else:
        container = base_content

    # if extract is at depth 2 or 3 we get its direct parent container
    if "container_slug" in kwargs_array:
        try:
            container = container.children_dict[kwargs_array["container_slug"]]
        except KeyError:
            raise Http404("Aucun conteneur trouvé.")
        else:
            if not isinstance(container, Container):
                raise Http404("Aucun conteneur trouvé.")
    elif container == base_content:
        # if we have no subcontainer, there is neither 'container_slug' nor "parent_container_slug
        return base_content
    if container is None:
        raise Http404("Aucun conteneur trouvé.")
    return container


def search_extract_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` and MUST contains\
    ``extract_slug``
    :return: the Extract object
    :rtype: zds.tutorialv2.models.versioned.Extract
    :raise: Http404 if not found
    """

    from zds.tutorialv2.models.versioned import Extract

    # if the extract is at a depth of 3 we get the first parent container
    container = search_container_or_404(base_content, kwargs_array)

    extract = None
    if "extract_slug" in kwargs_array:
        try:
            extract = container.children_dict[kwargs_array["extract_slug"]]
        except KeyError:
            raise Http404("Aucun extrait trouvé.")
        else:
            if not isinstance(extract, Extract):
                raise Http404("Aucun extrait trouvé.")
    return extract


def never_read(content, user=None):
    """Check if a content note feed has been read by a user since its last post was added.

    :param content: the content to check
    :type content: zds.tutorialv2.models.database.PublishableContent
    :param user: the user to test, if None, gets the current request user
    :type user: zds.member.models.User
    :return: ``True`` if the user never read this content's reactions, ``False`` otherwise
    :rtype: bool
    """

    from zds.tutorialv2.models.database import ContentRead

    if not user:
        user = get_current_user()

    if user and user.is_authenticated and content.last_note:
        return (
            ContentRead.objects.filter(note__pk=content.last_note.pk, content__pk=content.pk, user__pk=user.pk).count()
            == 0
        )
    elif not content.last_note:
        return False
    else:
        return True


def last_participation_is_old(content, user):
    from zds.tutorialv2.models.database import ContentReaction, ContentRead

    if user is None or not user.is_authenticated:
        return False
    if ContentReaction.objects.filter(author__pk=user.pk, related_content__pk=content.pk).count() == 0:
        return False
    return (
        ContentRead.objects.filter(note__pk=content.last_note.pk, content__pk=content.pk, user__pk=user.pk).count() == 0
    )


def mark_read(content, user=None):
    """Mark the last tutorial note as read for the user.

    :param content: the content to mark
    :param user: user that read the content, if ``None`` will use currrent user
    """

    from zds.tutorialv2.models.database import ContentReaction, ContentRead

    if not user:
        user = get_current_user()

    if user and user.is_authenticated:
        if content.last_note is not None:
            ContentRead.objects.filter(content__pk=content.pk, user__pk=user.pk).delete()
            a = ContentRead(note=content.last_note, content=content, user=user)
            a.save()
            signals.content_read.send(sender=content.__class__, instance=content, user=user, target=ContentReaction)


class TooDeepContainerError(ValueError):
    """
    Exception used to represent the fact you can't add a container to a level greater than two
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def try_adopt_new_child(adoptive_parent, child):
    """Try the adoptive parent to take the responsability of the child
    :param adoptive_parent: the new parent for child if all check pass
    :param child: content child to be moved
    :raise Http404: if adoptive_parent_full_path is not found on root hierarchy
    :raise TypeError: if the adoptive parent is not allowed to adopt the child due to its type
    :raise TooDeepContainerError: if the child is a container that is too deep to be adopted by the proposed parent
    """

    from zds.tutorialv2.models.versioned import Container, Extract

    if isinstance(child, Extract):
        if not adoptive_parent.can_add_extract():
            raise TypeError
    if isinstance(child, Container):
        if not adoptive_parent.can_add_container():
            raise TypeError
        if adoptive_parent.get_tree_depth() + child.get_tree_level() > settings.ZDS_APP["content"]["max_tree_depth"]:
            raise TooDeepContainerError
        if adoptive_parent.get_tree_depth() + child.get_tree_level() == settings.ZDS_APP["content"]["max_tree_depth"]:
            if child.can_add_container():  # if the child is a part with empty chapters
                # that we move inside another part
                raise TooDeepContainerError
    adoptive_parent.top_container().change_child_directory(child, adoptive_parent)


def get_target_tagged_tree(movable_child, root):
    """Gets the tagged tree with deplacement availability

    :param movable_child: the extract we want to move
    :param root: the VersionedContent we use as root
    :rtype: tuple
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child\
    check get_target_tagged_tree_for_extract and get_target_tagged_tree_for_container for format
    """

    from zds.tutorialv2.models.versioned import Extract

    if isinstance(movable_child, Extract):
        return get_target_tagged_tree_for_extract(movable_child, root)
    else:
        return get_target_tagged_tree_for_container(movable_child, root)


def get_target_tagged_tree_for_extract(movable_child, root):
    """Gets the tagged tree with displacement availability when movable_child is an extract

    :param movable_child: the extract we want to move
    :param root: the VersionedContent we use as root
    :rtype: tuple
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child\
    tuples are ``(relative_path, title, level, can_be_a_target)``
    """

    from zds.tutorialv2.models.versioned import Extract

    target_tagged_tree = []
    for child in root.traverse(False):
        if isinstance(child, Extract):
            target_tagged_tree.append(
                (child.get_full_slug(), child.title, child.get_tree_depth(), child != movable_child)
            )
        else:
            target_tagged_tree.append((child.get_path(True), child.title, child.get_tree_depth(), False))

    return target_tagged_tree


def get_target_tagged_tree_for_container(movable_child, root, bias=-1):
    """Gets the tagged tree with displacement availability when movable_child is an extract

    :param movable_child: the container we want to move
    :param root: the VersionedContent we use as root
    :param bias: a negative or zero integer that represent the level bias. A value of -1 (default) represent\
    the fact that we want to make the *movable_child* **a sibling** of the tagged child, a value of 0 that we want\
    to make it a sub child.
    :rtype: tuple
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child\
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
            elif level == 2 and movable_child.can_add_container():
                enabled = enabled and tested == root

            target_tagged_tree.append((child.get_path(True), child.title, child.get_tree_depth(), enabled))

    return target_tagged_tree


def normalize_unicode_url(unicode_url):
    """Sometimes you get an URL by a user that just isn't a real URL
    because it contains unsafe characters like 'β' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    .. sourcecode:: python

        normalize_unicode_url(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
        # 'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'


    :param charset: The target charset for the URL if the url was
                    given as unicode string.
    """
    scheme, netloc, path, querystring, anchor = urlsplit(unicode_url)
    path = quote(path, "/%")
    querystring = quote(querystring, ":&=")
    return urlunsplit((scheme, netloc, path, querystring, anchor))


class BadManifestError(Exception):
    """The exception that is raised when the manifest.json contains errors"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def get_content_from_json(json, sha, slug_last_draft, public=False, max_title_len=80, hint_licence=None):
    """Transform the JSON formated data into ``VersionedContent``

    :param json: JSON data from a `manifest.json` file
    :param sha: version
    :param slug_last_draft: the slug for draft marked version
    :param max_title_len: max str length for title
    :param public: the function will fill a PublicContent instead of a VersionedContent if `True`
    :param hint_licence: avoid loading the licence if it is already the same as the one loaded
    :return: a Public/VersionedContent with all the information retrieved from JSON
    :rtype: zds.tutorialv2.models.versioned.VersionedContent|zds.tutorialv2.models.database.PublishedContent
    """

    from zds.tutorialv2.models.versioned import Container, Extract, PublicContent, VersionedContent

    if "version" in json and json["version"] in (2, 2.1):  # add newest version of manifest
        if not all_is_string_appart_from_given_keys(json, ("children", "ready_to_publish", "version")):
            raise BadManifestError(_("Le fichier manifest n'est pas bien formaté."))
        # create and fill the container
        if len(json["title"]) > max_title_len:
            raise BadManifestError(
                _("Le titre doit être une chaîne de caractères de moins de {} caractères.").format(max_title_len)
            )

        # check that title gives correct slug
        slugify_raise_on_invalid(json["title"])

        if not check_slug(json["slug"]):
            raise InvalidSlugError(json["slug"])
        else:
            json_slug = json["slug"]

        if not public:
            versioned = VersionedContent(sha, "TUTORIAL", json["title"], json_slug, slug_last_draft)
        else:
            versioned = PublicContent(sha, "TUTORIAL", json["title"], json_slug)

        # fill metadata :
        if "description" in json:
            versioned.description = json["description"]

        if "type" in json:
            if json["type"] in CONTENT_TYPE_LIST:
                versioned.type = json["type"]

        if "licence" in json:
            if hint_licence is not None and hint_licence.code == json["licence"]:
                versioned.licence = hint_licence
            else:
                versioned.licence = Licence.objects.filter(code=json["licence"]).first()
        # Note: There is no fallback to a default license in case of problems.
        # The author will have to set it himself prior to publication.

        if "introduction" in json:
            versioned.introduction = json["introduction"]
        if "conclusion" in json:
            versioned.conclusion = json["conclusion"]

        # then, fill container with children
        fill_containers_from_json(json, versioned)
    else:
        # minimal support for deprecated manifest version 1
        # supported content types are exclusively ARTICLE and TUTORIAL

        if "type" in json:
            if json["type"] == "article":
                _type = "ARTICLE"
            else:
                _type = "TUTORIAL"
        else:
            _type = "ARTICLE"

        if not public:
            versioned = VersionedContent(sha, _type, json["title"], slug_last_draft)
        else:
            versioned = PublicContent(sha, _type, json["title"], slug_last_draft)

        if "description" in json:
            versioned.description = json["description"]
        if "introduction" in json:
            versioned.introduction = json["introduction"]
        if "conclusion" in json:
            versioned.conclusion = json["conclusion"]
        if "licence" in json:
            versioned.licence = Licence.objects.filter(code=json["licence"]).first()
        # Note: There is no fallback to a default license in case of problems.
        # The author will have to set it himself prior to publication.

        versioned.ready_to_publish = True  # the parent is always ready to publish
        if _type == "ARTICLE":
            extract = Extract("text", "")
            if "text" in json:
                extract.text = json["text"]  # probably 'text.md' !
            versioned.add_extract(extract, generate_slug=True)

        else:  # it's a tutorial
            if json["type"] == "MINI" and "chapter" in json and "extracts" in json["chapter"]:
                for extract in json["chapter"]["extracts"]:
                    new_extract = Extract(
                        extract["title"],
                        "{}_{}".format(extract["pk"], slugify_raise_on_invalid(extract["title"], True)),
                    )
                    if "text" in extract:
                        new_extract.text = extract["text"]
                    versioned.add_extract(new_extract, generate_slug=False)

            elif json["type"] == "BIG" and "parts" in json:
                for part in json["parts"]:
                    new_part = Container(
                        part["title"], "{}_{}".format(part["pk"], slugify_raise_on_invalid(part["title"], True))
                    )

                    if "introduction" in part:
                        new_part.introduction = part["introduction"]
                    if "conclusion" in part:
                        new_part.conclusion = part["conclusion"]
                    versioned.add_container(new_part, generate_slug=False)

                    if "chapters" in part:
                        for chapter in part["chapters"]:
                            new_chapter = Container(
                                chapter["title"],
                                "{}_{}".format(chapter["pk"], slugify_raise_on_invalid(chapter["title"], True)),
                            )

                            if "introduction" in chapter:
                                new_chapter.introduction = chapter["introduction"]
                            if "conclusion" in chapter:
                                new_chapter.conclusion = chapter["conclusion"]
                            new_part.add_container(new_chapter, generate_slug=False)

                            if "extracts" in chapter:
                                for extract in chapter["extracts"]:
                                    new_extract = Extract(
                                        extract["title"],
                                        "{}_{}".format(extract["pk"], slugify_raise_on_invalid(extract["title"], True)),
                                    )

                                    if "text" in extract:
                                        new_extract.text = extract["text"]
                                    new_chapter.add_extract(new_extract, generate_slug=False)

    return versioned


def fill_containers_from_json(json_sub, parent):
    """Function which call itself to fill container

    :param json_sub: dictionary from 'manifest.json'
    :param parent: the container to fill
    :raise BadManifestError: if the manifest is not well formed or the content's type is not correct
    :raise KeyError: if one mandatory key is missing
    """

    from zds.tutorialv2.models.versioned import Container, Extract

    if "children" in json_sub:
        for child in json_sub["children"]:
            if not all_is_string_appart_from_given_keys(child, ("children", "ready_to_publish")):
                raise BadManifestError(
                    _("Le fichier manifest n'est pas bien formaté dans le conteneur " + str(json_sub["title"]))
                )
            if child["object"] == "container":
                slug = ""
                try:
                    slug = child["slug"]
                    if not check_slug(slug):
                        raise InvalidSlugError(slug)
                except KeyError:
                    pass
                new_container = Container(child["title"], slug)
                if "introduction" in child:
                    new_container.introduction = child["introduction"]
                if "conclusion" in child:
                    new_container.conclusion = child["conclusion"]
                try:
                    parent.add_container(new_container, generate_slug=(slug == ""))
                except InvalidOperationError as e:
                    raise BadManifestError(e.message)
                new_container.ready_to_publish = child.get("ready_to_publish", True)
                if "children" in child:
                    fill_containers_from_json(child, new_container)
            elif child["object"] == "extract":
                slug = ""
                try:
                    slug = child["slug"]
                    if not check_slug(slug):
                        raise InvalidSlugError(child["slug"])
                except KeyError:
                    pass
                new_extract = Extract(child["title"], slug)

                if "text" in child:
                    new_extract.text = child["text"]
                try:
                    parent.add_extract(new_extract, generate_slug=(slug == ""))
                except InvalidOperationError as e:
                    raise BadManifestError(e.message)
            else:
                raise BadManifestError(_("Type d'objet inconnu : « {} »").format(child["object"]))


def init_new_repo(db_object, introduction_text="", conclusion_text="", commit_message="", do_commit=True):
    """Create a new repository in ``settings.ZDS_APP['contents']['private_repo']``\
     to store the files for a new content. Note that ``db_object.sha_draft`` will be set to the good value

    :param db_object: `PublishableContent` (WARNING: should have a valid ``slug``, so previously saved)
    :param introduction_text: introduction from form
    :param conclusion_text: conclusion from form
    :param commit_message: set a commit message instead of the default one
    :param do_commit: perform commit if ``True``
    :return: ``VersionedContent`` object
    :rtype: zds.tutorialv2.models.versioned.VersionedContent
    """

    from zds.tutorialv2.models.versioned import VersionedContent

    # create directory
    path = db_object.get_repo_path()
    if not os.path.isdir(path):
        os.makedirs(path, mode=0o777)

    # init repo:
    Repo.init(path, bare=False, template="")

    # create object
    versioned_content = VersionedContent(None, db_object.type, db_object.title, db_object.slug)

    # fill some information that are missing :
    versioned_content.licence = db_object.licence
    versioned_content.description = db_object.description

    # perform changes:
    if not commit_message:
        commit_message = "Création du contenu"

    sha = versioned_content.repo_update(
        db_object.title, introduction_text, conclusion_text, commit_message=commit_message, do_commit=do_commit
    )

    # update sha:
    if do_commit:
        db_object.sha_draft = sha
        db_object.sha_beta = None
        db_object.sha_public = None
        db_object.sha_validation = None

        db_object.save()

    return versioned_content


def clone_repo(old_path, new_path):
    """
    Proxy to ``git clone command``. Ensure directory are properly created

    :param old_path: path of the repo to be cloned
    :param new_path: path of the target repo
    :return: the target repository encapsulated in a ``GitPython`` object.
    :rtype: Repo
    """
    if not os.path.isdir(new_path):
        os.makedirs(new_path, mode=0o777)
    old_repo = Repo(old_path)
    new_repo = old_repo.clone(new_path)
    return new_repo


def get_commit_author():
    """get a dictionary that represent the commit author with ``author`` and ``comitter`` key. If there is no users,
    bot account pk is used.

    :return: correctly formatted commit author for ``repo.index.commit()``
    :rtype: dict
    """
    user = get_current_user()

    if user and user.is_authenticated:
        aut_user = str(user.pk)
        aut_email = None

        if hasattr(user, "email"):
            aut_email = user.email

    else:
        try:
            aut_user = str(User.objects.filter(username=settings.ZDS_APP["member"]["bot_account"]).first().pk)
        except AttributeError:  # if nothing is found, `first` returns None, which does not have attribute pk
            aut_user = "0"

        aut_email = None

    if aut_email is None or not aut_email.strip():
        aut_email = _("inconnu@{}").format(settings.ZDS_APP["site"]["dns"])

    return {"author": Actor(aut_user, aut_email), "committer": Actor(aut_user, aut_email)}


def export_extract(extract, with_text):
    """Export an extract to a dictionary

    :param extract: extract to export
    :return: dictionary containing the information
    :rtype: dict
    """
    dct = OrderedDict()
    dct["object"] = "extract"
    dct["slug"] = extract.slug
    dct["title"] = extract.title

    if extract.text and not with_text:
        dct["text"] = extract.text
    elif extract.text:
        dct["text"] = extract.get_text()
    elif with_text:
        dct["text"] = ""

    return dct


def export_container(container, with_text=False, ready_to_publish_only=False):
    """Export a container to a dictionary

    :param container: the container
    :type container: zds.tutorialv2.models.models_versioned.Container
    :param ready_to_publish_only: if True, returns only ready-to-publish containers
    :type ready_to_publish_only: boolean
    :return: dictionary containing the information
    :rtype: dict
    """
    dct = OrderedDict()
    dct["object"] = "container"
    dct["slug"] = container.slug
    dct["title"] = container.title

    if container.introduction and not with_text:
        dct["introduction"] = str(container.introduction)
    elif container.introduction:
        dct["introduction"] = container.get_introduction()
    elif with_text:
        dct["introduction"] = ""

    if container.conclusion and not with_text:
        dct["conclusion"] = str(container.conclusion)
    elif container.conclusion:
        dct["conclusion"] = container.get_conclusion()
    elif with_text:
        dct["conclusion"] = ""

    dct["children"] = []
    dct["ready_to_publish"] = container.ready_to_publish
    if container.has_sub_containers():
        for child in container.children:
            if ready_to_publish_only and not child.ready_to_publish:
                continue
            dct["children"].append(export_container(child, with_text, ready_to_publish_only))
    elif container.has_extracts():
        for child in container.children:
            dct["children"].append(export_extract(child, with_text))

    return dct


def export_content(content, with_text=False, ready_to_publish_only=False):
    """Export a content to dictionary in order to store them in a JSON file

    :param content: content to be exported
    :param ready_to_publish_only: if True, returns only ready-to-publish containers
    :type ready_to_publish_only: boolean
    :return: dictionary containing the information
    :rtype: dict
    """
    dct = export_container(content, with_text, ready_to_publish_only)

    # append metadata :
    dct["version"] = 2.1
    dct["description"] = content.description
    dct["type"] = content.type
    if content.licence:
        dct["licence"] = content.licence.code
    return dct


def default_slug_pool():
    """initialize a slug pool with all forbidden name. basically ``introduction`` and ``conclusion``

    :return: the forbidden slugs in the edition system
    :rtype: dict
    """

    return {"introduction": 1, "conclusion": 1}  # forbidden slugs


class InvalidOperationError(RuntimeError):
    pass


def get_blob(tree, path):
    """Return the data contained into a given file

    :param tree: Git Tree object
    :type tree: git.objects.tree.Tree
    :param path: Path to file
    :type path: str
    :return: contains
    :rtype: bytearray
    """
    # get all extracts
    for blob in tree.blobs:
        try:
            if os.path.abspath(blob.path) == os.path.abspath(path):
                data = blob.data_stream.read().decode()
                return data
        except OSError:  # in case of deleted files, or the system cannot get the lock, juste return ""
            return ""
    # traverse directories when we are at root or in a part or chapter
    if len(tree.trees) > 0:
        for subtree in tree.trees:
            result = get_blob(subtree, path)
            if result is not None:
                return result
        return None
    else:
        return None


class BadArchiveError(Exception):
    """The exception that is raised when a bad archive is sent"""

    message = ""

    def __init__(self, reason):
        self.message = reason


NamedUrl = namedtuple("NamedUrl", ["name", "url", "level"])


def get_content_version_url(versioned_content, version):
    route_parameters = {"pk": versioned_content.pk, "slug": versioned_content.slug, "version": version}
    url = reverse("content:view-version", kwargs=route_parameters)
    return url
