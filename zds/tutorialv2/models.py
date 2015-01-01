# coding: utf-8

from math import ceil
import shutil
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

from zds.gallery.models import Image, Gallery
from zds.utils import slugify, get_current_user
from zds.utils.models import SubCategory, Licence, Comment
from zds.utils.tutorials import get_blob
from zds.utils.tutorialv2 import export_content
from zds.settings import ZDS_APP
from zds.utils.models import HelpWriting


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

    # TODO: thumbnails ?

    def __init__(self, title, slug='', parent=None, position_in_parent=1):
        self.title = title
        self.slug = slug
        self.parent = parent
        self.position_in_parent = position_in_parent

        self.children = []  # even if you want, do NOT remove this line
        self.children_dict = {}

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

    def add_container(self, container, generate_slug=False):
        """
        Add a child Container, but only if no extract were previously added and tree depth is < 2.
        :param container: the new container
        :param generate_slug: if `True`, ask the top container an unique slug for this object
        """
        if not self.has_extracts():
            if self.get_tree_depth() < ZDS_APP['tutorial']['max_tree_depth']:
                if generate_slug:
                    container.slug = self.top_container().get_unique_slug(container.title)
                else:
                    self.top_container().add_slug_to_pool(container.slug)
                container.parent = self
                container.position_in_parent = self.get_last_child_position() + 1
                self.children.append(container)
                self.children_dict[container.slug] = container
            else:
                raise InvalidOperationError("Cannot add another level to this content")
        else:
            raise InvalidOperationError("Can't add a container if this container contains extracts.")
        # TODO: limitation if article ?

    def add_extract(self, extract, generate_slug=False):
        """
        Add a child container, but only if no container were previously added
        :param extract: the new extract
        :param generate_slug: if `True`, ask the top container an unique slug for this object
        """
        if not self.has_sub_containers():
            if generate_slug:
                extract.slug = self.top_container().get_unique_slug(extract.title)
            else:
                self.top_container().add_slug_to_pool(extract.slug)
            extract.container = self
            extract.position_in_parent = self.get_last_child_position() + 1
            self.children.append(extract)
            self.children_dict[extract.slug] = extract

    def update_children(self):
        """
        Update the path for introduction and conclusion for the container and all its children. If the children is an
        extract, update the path to the text instead. This function is useful when `self.pk` or `self.title` has
        changed.
        Note : this function does not account for a different arrangement of the files.
        """
        self.introduction = os.path.join(self.get_path(relative=True), "introduction.md")
        self.conclusion = os.path.join(self.get_path(relative=True), "conclusion.md")
        for child in self.children:
            if isinstance(child, Container):
                child.update_children()
            elif isinstance(child, Extract):
                child.text = child.get_path(relative=True)

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

    def get_introduction(self):
        """
        :return: the introduction from the file in `self.introduction`
        """
        if self.introduction:
            return get_blob(self.top_container().repository.commit(self.top_container().current_version).tree,
                            self.introduction)

    def get_introduction_online(self):
        """
        Get introduction content of the public version
        :return: the introduction
        """
        path = self.top_container().get_prod_path() + self.introduction + '.html'
        if os.path.exists(path):
            intro = open(path)
            intro_content = intro.read()
            intro.close()
            return intro_content.decode('utf-8')

    def get_conclusion(self):
        """
        :return: the conclusion from the file in `self.conclusion`
        """
        if self.introduction:
            return get_blob(self.top_container().repository.commit(self.top_container().current_version).tree,
                            self.conclusion)

    def get_conclusion_online(self):
        """
        Get conclusion content of the public version
        :return: the conclusion
        """
        path = self.top_container().get_prod_path() + self.conclusion + '.html'
        if os.path.exists(path):
            conclusion = open(path)
            conclusion_content = conclusion.read()
            conclusion.close()
            return conclusion_content.decode('utf-8')

    # TODO:
    # - get_absolute_url_*() stuffs (harder than it seems, because they cannot be written in a recursive way)
    # - the `maj_repo_*()` stuffs should probably be into the model ?


class Extract:
    """
    A content extract from a Container.

    It has a title, a position in the parent container and a text.
    """

    title = ''
    slug = ''
    container = None
    position_in_container = 1
    text = None

    def __init__(self, title, slug='', container=None, position_in_container=1):
        self.title = title
        self.slug = slug
        self.container = container
        self.position_in_container = position_in_container

    def __unicode__(self):
        return u'<Extrait \'{}\'>'.format(self.title)

    def get_absolute_url(self):
        """
        :return: the url to access the tutorial offline
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url(),
            self.position_in_container,
            slugify(self.title)
        )

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_online(),
            self.position_in_container,
            slugify(self.title)
        )

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_beta(),
            self.position_in_container,
            slugify(self.title)
        )

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the extract.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        return os.path.join(self.container.get_path(relative=relative), self.slug) + '.md'

    def get_prod_path(self):
        """
        Get the physical path to the public version of a specific version of the extract.
        :return: physical path
        """
        return os.path.join(self.container.get_prod_path(), self.slug) + '.md.html'
        # TODO: should this function exists ? (there will be no public version of a text, all in parent container)

    def get_text(self):
        """
        :return: versioned text
        """
        if self.text:
            return get_blob(
                self.container.top_container().repository.commit(self.container.top_container().current_version).tree,
                self.text)

    def get_text_online(self):
        """
        :return: public text of the extract
        """
        path = self.container.top_container().get_prod_path() + self.text + '.html'
        if os.path.exists(path):
            txt = open(path)
            txt_content = txt.read()
            txt.close()
            return txt_content.decode('utf-8')


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

    slug_pool = {}

    # Metadata from DB :
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
        self.repository = Repo(self.get_path())

        self.slug_pool = {'introduction': 1, 'conclusion': 1, slug: 1}  # forbidden slugs

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """
        :return: the url to access the tutorial when offline
        """
        return reverse('view-tutorial-url', args=[self.slug])

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return reverse('zds.tutorialv2.views.view_tutorial_online', args=[self.slug])

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        """
        if self.is_beta:
            return self.get_absolute_url() + '?version=' + self.sha_beta
        else:
            return self.get_absolute_url()

    def get_edit_url(self):
        """
        :return: the url to edit the tutorial
        """
        return reverse('zds.tutorialv2.views.modify_tutorial') + '?tutorial={0}'.format(self.slug)

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

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the Content.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        if relative:
            return ''
        else:
            # get the full path (with tutorial/article before it)
            return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_path'], self.slug)

    def get_prod_path(self):
        """
        Get the physical path to the public version of the content
        :return: physical path
        """
        return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_public_path'], self.slug)

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


def fill_containers_from_json(json_sub, parent):
    """
    Function which call itself to fill container
    :param json_sub: dictionary from "manifest.json"
    :param parent: the container to fill
    """
    # TODO should be static function of `VersionedContent`
    # TODO should implement fallbacks
    if 'children' in json_sub:
        for child in json_sub['children']:
            if child['object'] == 'container':
                new_container = Container(child['title'], child['slug'])
                if 'introduction' in child:
                    new_container.introduction = child['introduction']
                if 'conclusion' in child:
                    new_container.conclusion = child['conclusion']
                parent.add_container(new_container)
                if 'children' in child:
                    fill_containers_from_json(child, new_container)
            elif child['object'] == 'extract':
                new_extract = Extract(child['title'], child['slug'])
                new_extract.text = child['text']
                parent.add_extract(new_extract)
            else:
                raise Exception('Unknown object type'+child['object'])


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
    slug = models.SlugField(max_length=80)
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
            return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_path'], self.slug)

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

    def load_version(self, sha=None, public=False):
        """
        Using git, load a specific version of the content. if `sha` is `None`, the draft/public version is used (if
        `public` is `True`).
        Note: for practical reason, the returned object is filled with information form DB.
        :param sha: version
        :param public: if `True`, use `sha_public` instead of `sha_draft` if `sha` is `None`
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

        # create and fill the container
        versioned = VersionedContent(sha, self.type, json['title'], json['slug'])
        if 'version' in json and json['version'] == 2:
            # fill metadata :
            if 'description' in json:
                versioned.description = json['description']
            if json['type'] == 'ARTICLE' or json['type'] == 'TUTORIAL':
                versioned.type = json['type']
            else:
                versioned.type = self.type
            if 'licence' in json:
                versioned.licence = Licence.objects.filter(code=json['licence']).first()
            # TODO must default licence be enforced here ?
            if 'introduction' in json:
                versioned.introduction = json['introduction']
            if 'conclusion' in json:
                versioned.conclusion = json['conclusion']
            # then, fill container with children
            fill_containers_from_json(json, versioned)
            self.insert_data_in_versioned(versioned)

        else:
            raise Exception('Importation of old version is not yet supported')
            # TODO so here we can support old version !!

        return versioned

    def insert_data_in_versioned(self, versioned):
        """
        Insert some additional data from database in a VersionedContent
        :param versioned: the VersionedContent to fill
        """

        fns = [
            'have_markdown', 'have_html', 'have_pdf', 'have_epub', 'in_beta', 'in_validation', 'in_public',
            'authors', 'subcategory', 'image', 'creation_date', 'pubdate', 'update_date', 'source', 'sha_draft',
            'sha_beta', 'sha_validation', 'sha_public'
        ]

        # load functions and attributs in `versioned`
        for fn in fns:
            setattr(versioned, fn, getattr(self, fn))

        # general information
        versioned.is_beta = self.is_beta(versioned.current_version)
        versioned.is_validation = self.is_validation(versioned.current_version)
        versioned.is_public = self.is_public(versioned.current_version)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        # TODO ensure unique slug here !!

        super(PublishableContent, self).save(*args, **kwargs)

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
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".md"))

    def have_html(self):
        """
        Check if the html version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".html"))

    def have_pdf(self):
        """
        Check if the pdf version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".pdf"))

    def have_epub(self):
        """
        Check if the standard epub version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".epub"))

    def delete_entity_and_tree(self):
        """
        Delete the entities and their filesystem counterparts
        """
        shutil.rmtree(self.get_repo_path(), False)
        Validation.objects.filter(tutorial=self).delete()

        if self.gallery is not None:
            self.gallery.delete()
        if self.in_public():
            shutil.rmtree(self.get_prod_path())
        self.delete()


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
        return u'<Tutoriel "{0}" lu par {1}, #{2}>'.format(self.content,  self.user, self.note.pk)


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
