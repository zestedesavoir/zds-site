# coding: utf-8
import shutil
from collections import OrderedDict
from datetime import datetime
from urllib import urlretrieve
from urlparse import urlparse
try:
    import cairosvg
except ImportError:
    print('no cairo imported')

import os
from PIL import Image as ImagePIL
from django.contrib.auth.models import User
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from git import Repo, Actor
from lxml import etree
from uuslug import slugify

from zds import settings
from zds.notification import signals
from zds.tutorialv2 import REPLACE_IMAGE_PATTERN, VALID_SLUG
from zds.tutorialv2.models import CONTENT_TYPE_LIST
from zds.utils import get_current_user
from zds.utils import slugify as old_slugify
from zds.utils.models import Licence


def all_is_string_appart_from_children(dict_representation):
    """check all keys are string appart from the children key
    :param dict_representation: the json decoded dictionary
    :type dict_representation: dict
    :return:
    :rtype: bool
    """
    return all([isinstance(value, basestring) for key, value in dict_representation.items() if key != 'children'])


def search_container_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` keys\
    or the string representation
    :return: the Container object we were searching for
    :rtype: zds.tutorialv2.models.models_versioned.Container
    :raise Http404: if no suitable container is found
    """

    from zds.tutorialv2.models.models_versioned import Container

    if isinstance(kwargs_array, basestring):
        dic = {}
        dic['parent_container_slug'] = kwargs_array.split('/')[0]
        if len(kwargs_array.split('/')) >= 2:
            dic['container_slug'] = kwargs_array.split('/')[1]
        kwargs_array = dic

    if 'parent_container_slug' in kwargs_array:
            try:
                container = base_content.children_dict[kwargs_array['parent_container_slug']]
            except KeyError:
                raise Http404(u'Aucun conteneur trouvé.')
            else:
                if not isinstance(container, Container):
                    raise Http404(u'Aucun conteneur trouvé.')
    else:
        container = base_content

    # if extract is at depth 2 or 3 we get its direct parent container
    if 'container_slug' in kwargs_array:
        try:
            container = container.children_dict[kwargs_array['container_slug']]
        except KeyError:
            raise Http404(u'Aucun conteneur trouvé.')
        else:
            if not isinstance(container, Container):
                raise Http404(u'Aucun conteneur trouvé.')
    elif container == base_content:
        # if we have no subcontainer, there is neither 'container_slug' nor "parent_container_slug
        return base_content
    if container is None:
        raise Http404(u'Aucun conteneur trouvé.')
    return container


def search_extract_or_404(base_content, kwargs_array):
    """
    :param base_content: the base Publishable content we will use to retrieve the container
    :param kwargs_array: an array that may contain `parent_container_slug` and `container_slug` and MUST contains\
    ``extract_slug``
    :return: the Extract object
    :rtype: zds.tutorialv2.models.models_versioned.Extract
    :raise: Http404 if not found
    """

    from zds.tutorialv2.models.models_versioned import Extract

    # if the extract is at a depth of 3 we get the first parent container
    container = search_container_or_404(base_content, kwargs_array)

    extract = None
    if 'extract_slug' in kwargs_array:
        try:
            extract = container.children_dict[kwargs_array['extract_slug']]
        except KeyError:
            raise Http404(u'Aucun extrait trouvé.')
        else:
            if not isinstance(extract, Extract):
                raise Http404(u'Aucun extrait trouvé.')
    return extract


def never_read(content, user=None):
    """Check if a content note feed has been read by an user since its last post was added.

    :param content: the content to check
    :type content: zds.tutorialv2.models.models_database.PublishableContent
    :param user: the user to test, if None, gets the current request user
    :type user: zds.member.models.User
    :return: ``True`` if the user never read this content's reactions, ``False`` otherwise
    :rtype: bool
    """

    from zds.tutorialv2.models.models_database import ContentRead

    if not user:
        user = get_current_user()

    if user and user.is_authenticated() and content.last_note:
        return ContentRead.objects.filter(
            note__pk=content.last_note.pk, content__pk=content.pk, user__pk=user.pk).count() == 0
    elif not content.last_note:
        return False
    else:
        return True


def last_participation_is_old(content, user):
    from zds.tutorialv2.models.models_database import ContentRead, ContentReaction
    if user is None or not user.is_authenticated():
        return False
    if ContentReaction.objects.filter(author__pk=user.pk, related_content__pk=content.pk).count() == 0:
        return False
    return ContentRead.objects\
                      .filter(note__pk=content.last_note.pk, content__pk=content.pk, user__pk=user.pk)\
                      .count() == 0


def mark_read(content, user=None):
    """Mark the last tutorial note as read for the user.

    :param content: the content to mark
    :param user: user that read the content, if ``None`` will use currrent user
    """

    from zds.tutorialv2.models.models_database import ContentRead
    from zds.tutorialv2.models.models_database import ContentReaction

    if not user:
        user = get_current_user()

    if user and user.is_authenticated():
        if content.last_note is not None:
            ContentRead.objects.filter(
                content__pk=content.pk,
                user__pk=user.pk).delete()
            a = ContentRead(
                note=content.last_note,
                content=content,
                user=user)
            a.save()
            signals.content_read.send(sender=content.__class__, instance=content, user=user, target=ContentReaction)


class TooDeepContainerError(ValueError):
    """
    Exception used to represent the fact you can't add a container to a level greater than two
    """

    def __init__(self, *args, **kwargs):
        super(TooDeepContainerError, self).__init__(*args, **kwargs)


def try_adopt_new_child(adoptive_parent, child):
    """Try the adoptive parent to take the responsability of the child
    :param adoptive_parent: the new parent for child if all check pass
    :param child: content child to be moved
    :raise Http404: if adoptive_parent_full_path is not found on root hierarchy
    :raise TypeError: if the adoptive parent is not allowed to adopt the child due to its type
    :raise TooDeepContainerError: if the child is a container that is too deep to be adopted by the proposed parent
    """

    from zds.tutorialv2.models.models_versioned import Container, Extract

    if isinstance(child, Extract):
        if not adoptive_parent.can_add_extract():
            raise TypeError
    if isinstance(child, Container):
        if not adoptive_parent.can_add_container():
            raise TypeError
        if adoptive_parent.get_tree_depth() + child.get_tree_level() > settings.ZDS_APP['content']['max_tree_depth']:
            raise TooDeepContainerError
        if adoptive_parent.get_tree_depth() + child.get_tree_level() == settings.ZDS_APP['content']['max_tree_depth']:
            if child.can_add_container():  # if the child is a part with empty chapters
                # that we move inside another part
                raise TooDeepContainerError
    adoptive_parent.top_container().change_child_directory(child, adoptive_parent)


def get_target_tagged_tree(movable_child, root):
    """Gets the tagged tree with deplacement availability

    :param movable_child: the extract we want to move
    :param root: the VersionnedContent we use as root
    :rtype: tuple
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child\
    check get_target_tagged_tree_for_extract and get_target_tagged_tree_for_container for format
    """

    from zds.tutorialv2.models.models_versioned import Extract

    if isinstance(movable_child, Extract):
        return get_target_tagged_tree_for_extract(movable_child, root)
    else:
        return get_target_tagged_tree_for_container(movable_child, root)


def get_target_tagged_tree_for_extract(movable_child, root):
    """Gets the tagged tree with displacement availability when movable_child is an extract

    :param movable_child: the extract we want to move
    :param root: the VersionnedContent we use as root
    :rtype: tuple
    :return: an array of tuples that represent the capacity of movable_child to be moved near another child\
    tuples are ``(relative_path, title, level, can_be_a_target)``
    """

    from zds.tutorialv2.models.models_versioned import Extract

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


def retrieve_image(url, directory):
    """For a given image, retrieve it, transform it into PNG (if needed) and store it

    :param url: URL of the image (either local or online)
    :type url: str
    :param directory: place where the image will be stored
    :type directory: str
    :return: the 'transformed' path to the image
    :rtype: str
    """

    # parse URL
    parsed_url = urlparse(url)

    img_directory, img_basename = os.path.split(parsed_url.path)
    img_basename = img_basename.decode('utf-8')
    img_basename_splitted = img_basename.split('.')

    if len(img_basename_splitted) > 1:
        img_extension = img_basename_splitted[-1].lower()
        img_filename = '.'.join(img_basename_splitted[:-1])
    else:
        img_extension = ''
        img_filename = img_basename

    new_url = os.path.join('images', img_basename.replace(' ', '_'))
    new_url_as_png = os.path.join('images', img_filename.replace(' ', '_') + '.png')

    store_path = os.path.abspath(os.path.join(directory, new_url))  # destination

    if not img_basename or os.path.exists(store_path) or os.path.exists(os.path.join(directory, new_url_as_png)):
        # another image with the same name already exists (but assume the two are different)
        img_filename += '_' + str(datetime.now().microsecond)
        new_url = os.path.join('images', img_filename.replace(' ', '_') + '.' + img_extension)
        new_url_as_png = os.path.join('images', img_filename.replace(' ', '_') + '.png')
        store_path = os.path.abspath(os.path.join(directory, new_url))

    try:
        if parsed_url.scheme in ['http', 'https', 'ftp'] \
                or parsed_url.netloc[:3] == 'www' or parsed_url.path[:3] == 'www':
            urlretrieve(url, store_path)  # download online image
        else:  # it's a local image, coming from a gallery

            if url[0] == '/':  # because `os.path.join()` think it's an absolute path if it start with `/`
                url = url[1:]

            source_path = os.path.join(settings.BASE_DIR, url)
            if os.path.isfile(source_path):
                shutil.copy(source_path, store_path)
            else:
                raise IOError(source_path)  # ... will use the default image instead

        if img_extension == 'svg':  # if SVG, will transform it into PNG
            resize_svg(store_path)
            new_url = new_url_as_png
            cairosvg.svg2png(url=store_path, write_to=os.path.join(directory, new_url))
            os.remove(store_path)
        else:
            img = ImagePIL.open(store_path)
            if img_extension == 'gif' or not img_extension.strip():
                # if no extension or gif, will transform it into PNG !
                new_url = new_url_as_png
                img.save(os.path.join(directory, new_url))
                os.remove(store_path)

    except (IOError, KeyError):  # HTTP 404, image does not exists, or Pillow cannot read it !

        # will be overwritten anyway, so it's better to remove whatever it was, for security reasons :
        if os.path.exists(store_path):
            os.remove(store_path)

        img = ImagePIL.open(settings.ZDS_APP['content']['default_image'])
        new_url = new_url_as_png
        img.save(os.path.join(directory, new_url))

    return new_url


def resize_svg(source):
    """modify the SVG XML tree in order to resize the URL, to fit the maximum size allowed

    :param source: content (not parsed) of the SVG file
    :type source: str
    """

    max_size = int(settings.THUMBNAIL_ALIASES['']['content']['size'][0])
    tree = etree.parse(source)
    svg = tree.getroot()
    try:
        width = float(svg.attrib['width'])
        height = float(svg.attrib['height'])
    except (KeyError, ValueError):
        width = max_size
        height = max_size
    end_height = height
    end_width = width
    if width > max_size or height > max_size:
        if width > height:
            end_height = (height / width) * max_size
            end_width = max_size
        else:
            end_height = max_size
            end_width = (width / height) * max_size
    svg.attrib['width'] = str(end_width)
    svg.attrib['height'] = str(end_height)
    tree.write(source)


def retrieve_image_and_update_link(group, previous_urls, directory='.'):
    """For each image link, update it (if possible)

    :param group: matching object
    :type group: re.MatchObject
    :param previous_urls: dictionary containing the previous urls and the transformed ones (in order to avoid treating\
    the same image two times !)
    :param directory: place where all image will be stored
    :type directory: str
    :type previous_urls: dict
    :return: updated link
    :rtype: str
    """

    # retrieve groups:
    start = group.group('start')
    url = group.group('url')
    txt = group.group('text')
    end = group.group('end')

    # look for image URL, and make it if needed
    if url not in previous_urls:
        new_url = retrieve_image(url, directory=directory)
        previous_urls[url] = new_url

    return start + txt + previous_urls[url] + end


def retrieve_and_update_images_links(md_text, directory='.'):
    """Find every image links and update them with `update_image_link()`.

    :param md_text: markdown text
    :type md_text: str
    :param directory: place where all image will be stored
    :type directory: str
    :return: the markdown with the good links
    :rtype: str
    """

    image_directory_path = os.path.join(directory, 'images')  # directory where the images will be stored

    if not os.path.isdir(image_directory_path):
        os.makedirs(image_directory_path)  # make the directory if needed

    previous_urls = {}
    new_text = REPLACE_IMAGE_PATTERN.sub(
        lambda g: retrieve_image_and_update_link(g, previous_urls, directory), md_text)

    return new_text


class BadManifestError(Exception):
    """ The exception that is raised when the manifest.json contains errors """

    def __init__(self, *args, **kwargs):
        super(BadManifestError, self).__init__(*args, **kwargs)


def get_content_from_json(json, sha, slug_last_draft, public=False, max_title_len=80):
    """Transform the JSON formated data into ``VersionedContent``

    :param json: JSON data from a `manifest.json` file
    :param sha: version
    :param slug_last_draft: the slug for draft marked version
    :param max_title_len: max str length for title
    :param public: the function will fill a PublicContent instead of a VersionedContent if `True`
    :return: a Public/VersionedContent with all the information retrieved from JSON
    :rtype: models.models_versioned.VersionedContent|models.models_database.PublishedContent
    """

    from zds.tutorialv2.models.models_versioned import Container, Extract, VersionedContent, PublicContent

    if 'version' in json and json['version'] == 2:
        json['version'] = '2'
        if not all_is_string_appart_from_children(json):
            json['version'] = 2
            raise BadManifestError(_(u"Le fichier manifest n'est pas bien formaté."))
        json['version'] = 2
        # create and fill the container
        if len(json['title']) > max_title_len:
            raise BadManifestError(
                _(u'Le titre doit être une chaîne de caractères de moins de {} caractères.').format(max_title_len))

        # check that title gives correct slug
        slugify_raise_on_invalid(json['title'])

        if not check_slug(json['slug']):
            raise InvalidSlugError(json['slug'])
        else:
            json_slug = json['slug']

        if not public:
            versioned = VersionedContent(sha, 'TUTORIAL', json['title'], json_slug, slug_last_draft)
        else:
            versioned = PublicContent(sha, 'TUTORIAL', json['title'], json_slug)

        # fill metadata :
        if 'description' in json:
            versioned.description = json['description']

        if 'type' in json:
            if json['type'] in CONTENT_TYPE_LIST:
                versioned.type = json['type']

        if 'licence' in json:
            versioned.licence = Licence.objects.filter(code=json['licence']).first()

        if 'licence' not in json or not versioned.licence:
            versioned.licence = Licence.objects.filter(pk=settings.ZDS_APP['content']['default_licence_pk']).first()

        if 'introduction' in json:
            versioned.introduction = json['introduction']
        if 'conclusion' in json:
            versioned.conclusion = json['conclusion']

        # then, fill container with children
        fill_containers_from_json(json, versioned)
    else:
        # minimal support for deprecated manifest version 1
        # supported content types are exclusively ARTICLE and TUTORIAL

        if 'type' in json:
            if json['type'] == 'article':
                _type = 'ARTICLE'
            else:
                _type = 'TUTORIAL'
        else:
            _type = 'ARTICLE'

        if not public:
            versioned = VersionedContent(sha, _type, json['title'], slug_last_draft)
        else:
            versioned = PublicContent(sha, _type, json['title'], slug_last_draft)

        if 'description' in json:
            versioned.description = json['description']
        if 'introduction' in json:
            versioned.introduction = json['introduction']
        if 'conclusion' in json:
            versioned.conclusion = json['conclusion']
        if 'licence' in json:
            versioned.licence = Licence.objects.filter(code=json['licence']).first()

        if 'licence' not in json or not versioned.licence:
            versioned.licence = Licence.objects.filter(pk=settings.ZDS_APP['content']['default_licence_pk']).first()

        if _type == 'ARTICLE':
            extract = Extract('text', '')
            if 'text' in json:
                extract.text = json['text']  # probably 'text.md' !
            versioned.add_extract(extract, generate_slug=True)

        else:  # it's a tutorial
            if json['type'] == 'MINI' and 'chapter' in json and 'extracts' in json['chapter']:
                for extract in json['chapter']['extracts']:
                    new_extract = Extract(
                        extract['title'],
                        '{}_{}'.format(extract['pk'], slugify_raise_on_invalid(extract['title'], True)))
                    if 'text' in extract:
                        new_extract.text = extract['text']
                    versioned.add_extract(new_extract, generate_slug=False)

            elif json['type'] == 'BIG' and 'parts' in json:
                for part in json['parts']:
                    new_part = Container(
                        part['title'], '{}_{}'.format(part['pk'], slugify_raise_on_invalid(part['title'], True)))

                    if 'introduction' in part:
                        new_part.introduction = part['introduction']
                    if 'conclusion' in part:
                        new_part.conclusion = part['conclusion']
                    versioned.add_container(new_part, generate_slug=False)

                    if 'chapters' in part:
                        for chapter in part['chapters']:
                            new_chapter = Container(
                                chapter['title'],
                                '{}_{}'.format(chapter['pk'], slugify_raise_on_invalid(chapter['title'], True)))

                            if 'introduction' in chapter:
                                new_chapter.introduction = chapter['introduction']
                            if 'conclusion' in chapter:
                                new_chapter.conclusion = chapter['conclusion']
                            new_part.add_container(new_chapter, generate_slug=False)

                            if 'extracts' in chapter:
                                for extract in chapter['extracts']:
                                    new_extract = Extract(
                                        extract['title'],
                                        '{}_{}'.format(extract['pk'], slugify_raise_on_invalid(extract['title'], True)))

                                    if 'text' in extract:
                                        new_extract.text = extract['text']
                                    new_chapter.add_extract(new_extract, generate_slug=False)

    return versioned


class InvalidSlugError(ValueError):
    """ Error raised when a slug is invalid. Argument is the slug that cause the error.

    ``source`` can also be provided, being the sentence from witch the slug was generated, if any.
    ``had_source`` is set to ``True`` if the source is provided.

    """

    def __init__(self, *args, **kwargs):

        self.source = ''
        self.had_source = False

        if 'source' in kwargs:
            self.source = kwargs.pop('source')
            self.had_source = True

        super(InvalidSlugError, self).__init__(*args, **kwargs)


def check_slug(slug):
    """
    If the title is incorrect (only special chars so slug is empty).

    :param slug: slug to test
    :type slug: str
    :return: `True` if slug is valid, false otherwise
    :rtype: bool
    """

    if not VALID_SLUG.match(slug):
        return False

    if not slug.replace('-', '').replace('_', ''):
        return False

    if len(slug) > settings.ZDS_APP['content']['maximum_slug_size']:
        return False

    return True


def slugify_raise_on_invalid(title, use_old_slugify=False):
    """
    use uuslug to generate a slug but if the title is incorrect (only special chars or slug is empty), an exception
    is raised.

    :param title: to be slugified title
    :type title: str
    :param use_old_slugify: use the function `slugify()` defined in zds.utils instead of the one in uuslug. Usefull \
    for retro-compatibility with the old article/tutorial module, SHOULD NOT be used for the new one !
    :type use_old_slugify: bool
    :raise InvalidSlugError: on incorrect slug
    :return: the slugified title
    :rtype: str
    """

    if not isinstance(title, basestring):
        raise InvalidSlugError('', source=title)
    if not use_old_slugify:
        slug = slugify(title)
    else:
        slug = old_slugify(title)

    if not check_slug(slug):
        raise InvalidSlugError(slug, source=title)

    return slug


def fill_containers_from_json(json_sub, parent):
    """Function which call itself to fill container

    :param json_sub: dictionary from 'manifest.json'
    :param parent: the container to fill
    :raise BadManifestError: if the manifest is not well formed or the content's type is not correct
    :raise KeyError: if one mandatory key is missing
    """

    from zds.tutorialv2.models.models_versioned import Container, Extract

    if 'children' in json_sub:

        for child in json_sub['children']:
            if not all_is_string_appart_from_children(child):
                raise BadManifestError(
                    _(u"Le fichier manifest n'est pas bien formaté dans le conteneur " + str(json_sub['title'])))
            if child['object'] == 'container':
                slug = ''
                try:
                    slug = child['slug']
                    if not check_slug(slug):
                        raise InvalidSlugError(slug)
                except KeyError:
                    pass
                new_container = Container(child['title'], slug)
                if 'introduction' in child:
                    new_container.introduction = child['introduction']
                if 'conclusion' in child:
                    new_container.conclusion = child['conclusion']
                try:
                    parent.add_container(new_container, generate_slug=(slug == ''))
                except InvalidOperationError as e:
                    raise BadManifestError(e.message)
                if 'children' in child:
                    fill_containers_from_json(child, new_container)
            elif child['object'] == 'extract':
                slug = ''
                try:
                    slug = child['slug']
                    if not check_slug(slug):
                        raise InvalidSlugError(child['slug'])
                except KeyError:
                    pass
                new_extract = Extract(child['title'], slug)

                if 'text' in child:
                    new_extract.text = child['text']
                try:
                    parent.add_extract(new_extract, generate_slug=(slug == ''))
                except InvalidOperationError as e:
                    raise BadManifestError(e.message)
            else:
                raise BadManifestError(_(u"Type d'objet inconnu : « {} »").format(child['object']))


def init_new_repo(db_object, introduction_text, conclusion_text, commit_message='', do_commit=True):
    """Create a new repository in ``settings.ZDS_APP['contents']['private_repo']``\
     to store the files for a new content. Note that ``db_object.sha_draft`` will be set to the good value

    :param db_object: `PublishableContent` (WARNING: should have a valid ``slug``, so previously saved)
    :param introduction_text: introduction from form
    :param conclusion_text: conclusion from form
    :param commit_message: set a commit message instead of the default one
    :param do_commit: perform commit if ``True``
    :return: ``VersionedContent`` object
    :rtype: zds.tutorialv2.models.models_versioned.VersionedContent
    """

    from zds.tutorialv2.models.models_versioned import VersionedContent

    # create directory
    path = db_object.get_repo_path()
    if not os.path.isdir(path):
        os.makedirs(path, mode=0o777)

    # init repo:
    Repo.init(path, bare=False, template='')

    # create object
    versioned_content = VersionedContent(None, db_object.type, db_object.title, db_object.slug)

    # fill some information that are missing :
    versioned_content.licence = db_object.licence
    versioned_content.description = db_object.description

    # perform changes:
    if not commit_message:
        commit_message = u'Création du contenu'

    sha = versioned_content.repo_update(
        db_object.title, introduction_text, conclusion_text, commit_message=commit_message, do_commit=do_commit)

    # update sha:
    if do_commit:
        db_object.sha_draft = sha
        db_object.sha_beta = None
        db_object.sha_public = None
        db_object.sha_validation = None

        db_object.save()

    return versioned_content


def get_commit_author():
    """get a dictionary that represent the commit author with ``author`` and ``comitter`` key. If there is no users,
    bot account pk is used.

    :return: correctly formatted commit author for ``repo.index.commit()``
    :rtype: dict
    """
    user = get_current_user()

    if user and user.is_authenticated():
        aut_user = str(user.pk)
        aut_email = None

        if hasattr(user, 'email'):
            aut_email = user.email

    else:
        try:
            aut_user = str(User.objects.filter(username=settings.ZDS_APP['member']['bot_account']).first().pk)
        except AttributeError:
            aut_user = '0'

        aut_email = None

    if aut_email is None or not aut_email.strip():
        aut_email = _(u'inconnu@{}').format(settings.ZDS_APP['site']['dns'])

    return {'author': Actor(aut_user, aut_email), 'committer': Actor(aut_user, aut_email)}


def export_extract(extract):
    """Export an extract to a dictionary

    :param extract: extract to export
    :return: dictionary containing the information
    :rtype: dict
    """
    dct = OrderedDict()
    dct['object'] = 'extract'
    dct['slug'] = extract.slug
    dct['title'] = extract.title

    if extract.text:
        dct['text'] = extract.text

    return dct


def export_container(container):
    """Export a container to a dictionary

    :param container: the container
    :return: dictionary containing the information
    :rtype: dict
    """
    dct = OrderedDict()
    dct['object'] = 'container'
    dct['slug'] = container.slug
    dct['title'] = container.title

    if container.introduction:
        dct['introduction'] = container.introduction

    if container.conclusion:
        dct['conclusion'] = container.conclusion

    dct['children'] = []

    if container.has_sub_containers():
        for child in container.children:
            dct['children'].append(export_container(child))
    elif container.has_extracts():
        for child in container.children:
            dct['children'].append(export_extract(child))

    return dct


def export_content(content):
    """Export a content to dictionary in order to store them in a JSON file

    :param content: content to be exported
    :return: dictionary containing the information
    :rtype: dict
    """
    dct = export_container(content)

    # append metadata :
    dct['version'] = 2  # to recognize old and new version of the content
    dct['description'] = content.description
    dct['type'] = content.type
    if content.licence:
        dct['licence'] = content.licence.code

    return dct


def default_slug_pool():
    """initialize a slug pool with all forbidden name. basically ``introduction`` and ``conclusion``

    :return: the forbidden slugs in the edition system
    :rtype: dict
    """

    return {'introduction': 1, 'conclusion': 1}  # forbidden slugs


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
                data = blob.data_stream.read()
                return data
        except (OSError, IOError):  # in case of deleted files, or the system cannot get the lock, juste return ""
            return ''
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
    """ The exception that is raised when a bad archive is sent """
    message = u''

    def __init__(self, reason):
        self.message = reason
