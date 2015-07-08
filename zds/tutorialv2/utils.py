# coding: utf-8
import shutil
import zipfile
import os
from datetime import datetime
import copy
from urllib import urlretrieve
from urlparse import urlparse
import codecs
from collections import OrderedDict

from git import Repo, Actor
import cairosvg
from lxml import etree
from PIL import Image as ImagePIL
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from zds.search.models import SearchIndexContent
from zds.search.utils import reindex_content
from zds.tutorialv2 import REPLACE_IMAGE_PATTERN
from zds import settings
from zds.settings import ZDS_APP
from zds.utils import get_current_user, slugify
from zds.utils.models import Licence
from zds.utils.templatetags.emarkdown import emarkdown


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
                raise Http404("No container found.")
            else:
                if not isinstance(container, Container):
                    raise Http404("No container found.")
    else:
        container = base_content

    # if extract is at depth 2 or 3 we get its direct parent container
    if 'container_slug' in kwargs_array:
        try:
            container = container.children_dict[kwargs_array['container_slug']]
        except KeyError:
            raise Http404("No container found.")
        else:
            if not isinstance(container, Container):
                raise Http404("No container found.")
    elif container == base_content:
        # if we have no subcontainer, there is neither "container_slug" nor "parent_container_slug
        return base_content
    if container is None:
        raise Http404("No container found.")
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
            raise Http404("No extract found.")
        else:
            if not isinstance(extract, Extract):
                raise Http404("No extract found.")
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


def mark_read(content, user=None):
    """Mark the last tutorial note as read for the user.

    :param content: the content to mark
    """

    from zds.tutorialv2.models.models_database import ContentRead

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


class TooDeepContainerError(ValueError):
    """
    Exception used to represent the fact you can't add a container to a level greater than two
    """

    def __init__(self, *args, **kwargs):
        super(TooDeepContainerError, self).__init__(*args, **kwargs)


def try_adopt_new_child(adoptive_parent, child):
    """Try the adoptive parent to take the responsability of the child

    :param parent_full_path:
    :param child_slug:
    :param root:
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
    :return: the "transformed" path to the image
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

    if img_basename == '' or os.path.exists(store_path) or os.path.exists(os.path.join(directory, new_url_as_png)):
        # another image with the same name already exists (but assume the two are different)
        img_filename += "_" + str(datetime.now().microsecond)
        new_url = os.path.join('images', img_filename.replace(' ', '_') + '.' + img_extension)
        new_url_as_png = os.path.join('images', img_filename.replace(' ', '_') + '.png')
        store_path = os.path.abspath(os.path.join(directory, new_url))

    try:
        if parsed_url.scheme in ["http", "https", "ftp"] \
                or parsed_url.netloc[:3] == "www" or parsed_url.path[:3] == "www":
            urlretrieve(url, store_path)  # download online image
        else:  # it's a local image, coming from a gallery

            if url[0] == '/':  # because `os.path.join()` think it's an absolute path if it start with `/`
                url = url[1:]

            source_path = os.path.join(settings.BASE_DIR, url)
            if os.path.isfile(source_path):
                shutil.copy(source_path, store_path)
            else:
                raise IOError(source_path)  # ... will use the default image instead

        if img_extension == "svg":  # if SVG, will transform it into PNG
            resize_svg(store_path)
            new_url = new_url_as_png
            cairosvg.svg2png(url=store_path, write_to=os.path.join(directory, new_url))
            os.remove(store_path)
        else:
            img = ImagePIL.open(store_path)
            if img_extension == "gif" or img_extension.strip() == '':
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

    max_size = int(settings.THUMBNAIL_ALIASES[""]["content"]["size"][0])
    tree = etree.parse(source)
    svg = tree.getroot()
    try:
        width = float(svg.attrib["width"])
        height = float(svg.attrib["height"])
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
    svg.attrib["width"] = str(end_width)
    svg.attrib["height"] = str(end_height)
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
    start = group.group("start")
    url = group.group("url")
    txt = group.group("text")
    end = group.group("end")

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

    from zds.tutorialv2.models.models_versioned import Container

    if not isinstance(container, Container):
        raise FailureDuringPublication(_(u'Le conteneur n\'en est pas un !'))

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
        f = codecs.open(os.path.join(base_dir, container.get_prod_path(relative=True)), 'w', encoding='utf-8')

        try:
            f.write(parsed)
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
            f = codecs.open(os.path.join(base_dir, path), 'w', encoding='utf-8')

            try:
                f.write(emarkdown(container.get_introduction(), db_object.js_support))
            except (UnicodeError, UnicodeEncodeError):
                raise FailureDuringPublication(
                    _(u'Une erreur est survenue durant la publication de l\'introduction de « {} »,'
                      u' vérifiez le code markdown').format(container.title))

            container.introduction = path

        if container.conclusion:
            path = os.path.join(container.get_prod_path(relative=True), 'conclusion.html')
            f = codecs.open(os.path.join(base_dir, path), 'w', encoding='utf-8')

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
    :rtype: zds.tutorialv2.models.models_database.PublishedContent
    """

    from zds.tutorialv2.models.models_database import PublishedContent

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
    parsed_with_local_images = retrieve_and_update_images_links(parsed, directory=extra_contents_path)

    md_file_path = base_name + '.md'
    md_file = codecs.open(md_file_path, 'w', encoding='utf-8')
    try:
        md_file.write(parsed_with_local_images)
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
    if ZDS_APP['content']['build_pdf_when_published']:
        os.system(
            settings.PANDOC_LOC + "pandoc " + settings.PANDOC_PDF_PARAM + " " +
            md_file_path + " -o " + base_name + ".pdf" + pandoc_debug_str)

    os.chdir(settings.BASE_DIR)

    # ok, now we can really publish the thing !
    is_update = False

    if db_object.public_version:
        public_version = db_object.public_version
        is_update = True

        # the content have been published in the past, so clean old files !
        old_path = public_version.get_prod_path()
        shutil.rmtree(old_path)

        # if the slug change, instead of using the same object, a new one will be created
        if versioned.slug != public_version.content_public_slug:
            public_version.must_redirect = True  # set redirection
            public_version.save()
            db_object.public_version = PublishedContent()
            public_version = db_object.public_version

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
    if is_major_update or not is_update:
        public_version.publication_date = datetime.now()

    public_version.sha_public = versioned.current_version
    public_version.save()
    try:
        make_zip_file(public_version)
    except IOError:
        pass

    # Launching index
    reindex_content(versioned, db_object)

    return public_version


def make_zip_file(published_content):
    """Create the zip archive extra content from the published content

    :param published_content: a PublishedContent object
    :return:
    """

    publishable = published_content.content
    path = os.path.join(published_content.get_extra_contents_directory(),
                        published_content.content_public_slug + ".zip")
    zip_file = zipfile.ZipFile(path, 'w')
    versioned = publishable.load_version(None, True)
    from zds.tutorialv2.views.views_contents import DownloadContent
    DownloadContent.insert_into_zip(zip_file, versioned.repository.commit(versioned.current_version).tree)
    zip_file.close()


def unpublish_content(db_object):
    """Remove the given content from the public view

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :return: ``True`` if unpublished, ``False`` otherwise
    :rtype: bool
    """

    from zds.tutorialv2.models.models_database import PublishedContent

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

        # We just delete all index that correspond to the content
        SearchIndexContent.objects.filter(publishable_content=db_object).delete()

        return True

    except (ObjectDoesNotExist, IOError):
        pass

    return False


class BadManifestError(Exception):
    """ The exception that is raised when the manifest.json contains errors """

    def __init__(self, *args, **kwargs):
        super(BadManifestError, self).__init__(*args, **kwargs)


def get_content_from_json(json, sha, slug_last_draft, public=False):
    """Transform the JSON formated data into ``VersionedContent``

    :param json: JSON data from a `manifest.json` file
    :param sha: version
    :param public: the function will fill a PublicContent instead of a VersionedContent if `True`
    :return: a Public/VersionedContent with all the information retrieved from JSON
    :rtype: models.models_versioned.VersionedContent|models.models_database.PublishedContent
    """

    from zds.tutorialv2.models.models_versioned import Container, Extract, VersionedContent, PublicContent

    if 'version' in json and json['version'] == 2:
        # create and fill the container
        if not public:
            versioned = VersionedContent(sha, 'TUTORIAL', json['title'], json['slug'], slug_last_draft)
        else:
            versioned = PublicContent(sha, 'TUTORIAL', json['title'], json['slug'])

        # fill metadata :
        if 'description' in json:
            versioned.description = json['description']

        if 'type' in json:
            if json['type'] == 'ARTICLE' or json['type'] == 'TUTORIAL':
                versioned.type = json['type']

        if 'licence' in json:
            versioned.licence = Licence.objects.filter(code=json['licence']).first()
        else:
            versioned.licence = Licence.objects.filter(pk=settings.ZDS_APP['content']['default_license_pk']).first()

        if 'introduction' in json:
            versioned.introduction = json['introduction']
        if 'conclusion' in json:
            versioned.conclusion = json['conclusion']

        # then, fill container with children
        fill_containers_from_json(json, versioned)
    else:
        # MINIMUM (!) fallback for version 1.0
        if "type" in json:
            if json['type'] == 'article':
                _type = 'ARTICLE'
            else:
                _type = "TUTORIAL"
        else:
            _type = "ARTICLE"

        if not public:
            versioned = VersionedContent(sha, _type, json['title'], slug_last_draft)
        else:
            versioned = PublicContent(sha, _type, json['title'], slug_last_draft)

        if 'description' in json:
            versioned.description = json['description']
        if "introduction" in json:
            versioned.introduction = json["introduction"]
        if "conclusion" in json:
            versioned.conclusion = json["conclusion"]
        if 'licence' in json:
            versioned.licence = Licence.objects.filter(code=json['licence']).first()
        else:
            versioned.licence = Licence.objects.filter(pk=settings.ZDS_APP['content']['default_license_pk']).first()

        if _type == 'ARTICLE':
            extract = Extract("text", '')
            if 'text' in json:
                extract.text = json['text']  # probably "text.md" !
            versioned.add_extract(extract, generate_slug=True)

        else:  # it's a tutorial
            if json['type'] == 'MINI' and 'chapter' in json and 'extracts' in json['chapter']:
                for extract in json['chapter']['extracts']:
                    new_extract = Extract(extract['title'], '{}_{}'.format(extract['pk'], slugify(extract['title'])))
                    if 'text' in extract:
                        new_extract.text = extract['text']
                    versioned.add_extract(new_extract, generate_slug=False)

            elif json['type'] == 'BIG' and 'parts' in json:
                for part in json['parts']:
                    new_part = Container(part['title'], '{}_{}'.format(part['pk'], slugify(part['title'])))
                    if 'introduction' in part:
                        new_part.introduction = part['introduction']
                    if 'conclusion' in part:
                        new_part.conclusion = part['conclusion']
                    versioned.add_container(new_part, generate_slug=False)

                    if 'chapters' in part:
                        for chapter in part['chapters']:
                            new_chapter = Container(
                                chapter['title'], '{}_{}'.format(chapter['pk'], slugify(chapter['title'])))
                            if 'introduction' in chapter:
                                new_chapter.introduction = chapter['introduction']
                            if 'conclusion' in chapter:
                                new_chapter.conclusion = chapter['conclusion']
                            new_part.add_container(new_chapter, generate_slug=False)

                            if 'extracts' in chapter:
                                for extract in chapter['extracts']:
                                    new_extract = Extract(
                                        extract['title'], '{}_{}'.format(extract['pk'], slugify(extract['title'])))
                                    if 'text' in extract:
                                        new_extract.text = extract['text']
                                    new_chapter.add_extract(new_extract, generate_slug=False)

    return versioned


def fill_containers_from_json(json_sub, parent):
    """Function which call itself to fill container

    :param json_sub: dictionary from "manifest.json"
    :param parent: the container to fill
    :raise BadManifestError: if the manifest is not well formed or the content's type is not correct
    :raise KeyError: if one mandatory key is missing
    """

    from zds.tutorialv2.models.models_versioned import Container, Extract

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
                raise BadManifestError(_(u'Type d\'objet inconnu : « {} »').format(child['object']))


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
    Repo.init(path, bare=False)

    # create object
    versioned_content = VersionedContent(None, db_object.type, db_object.title, db_object.slug)

    # fill some information that are missing :
    versioned_content.licence = db_object.licence
    versioned_content.description = db_object.description

    # perform changes:
    if commit_message == '':
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
    """get a dictionary that represent the commit author with ``author`` and ``comitter`` key

    :return: correctly formatted commit author for ``repo.index.commit()``
    :rtype: dict
    """
    user = get_current_user()

    if user:
        aut_user = str(user.pk)
        aut_email = None

        if hasattr(user, 'email'):
            aut_email = user.email

    else:
        aut_user = ZDS_APP['member']['bot_account']
        aut_email = None

    if aut_email is None or aut_email.strip() == "":
        aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
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
    dct['object'] = "container"
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
    for blob in tree.blobs:
        try:
            if os.path.abspath(blob.path) == os.path.abspath(path):
                data = blob.data_stream.read()
                return data
        except (OSError, IOError):
            return ""
    if len(tree.trees) > 0:
        for subtree in tree.trees:
            result = get_blob(subtree, path)
            if result is not None:
                return result
        return None
    else:
        return None
