# coding: utf-8

from math import ceil
import shutil
try:
    import ujson as json_reader
except:
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

    pk = 0
    title = ''
    slug = ''
    introduction = None
    conclusion = None
    parent = None
    position_in_parent = 1
    children = []

    # TODO: thumbnails ?

    def __init__(self, pk, title, parent=None, position_in_parent=1):
        self.pk = pk
        self.title = title
        self.slug = slugify(title)
        self.parent = parent
        self.position_in_parent = position_in_parent
        self.children = []  # even if you want, do NOT remove this line

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

    def add_container(self, container):
        """
        Add a child Container, but only if no extract were previously added and tree depth is < 2.
        :param container: the new container
        """
        if not self.has_extracts():
            if self.get_tree_depth() < ZDS_APP['tutorial']['max_tree_depth']:
                container.parent = self
                container.position_in_parent = self.get_last_child_position() + 1
                self.children.append(container)
            else:
                raise InvalidOperationError("Cannot add another level to this content")
        else:
            raise InvalidOperationError("Can't add a container if this container contains extracts.")
        # TODO: limitation if article ?

    def add_extract(self, extract):
        """
        Add a child container, but only if no container were previously added
        :param extract: the new extract
        """
        if not self.has_sub_containers():
            extract.container = self
            extract.position_in_parent = self.get_last_child_position() + 1
            self.children.append(extract)

    def get_phy_slug(self):
        """
        :return: the physical slug, used to represent data in filesystem
        """
        return str(self.pk) + '_' + self.slug

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
        return os.path.join(base, self.get_phy_slug())

    def get_prod_path(self):
        """
        Get the physical path to the public version of the container.
        Note: this function rely on the fact that the top container is VersionedContainer.
        :return: physical path
        """
        base = ''
        if self.parent:
            base = self.parent.get_prod_path()
        return os.path.join(base, self.get_phy_slug())

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
    container = None
    position_in_container = 1
    text = None
    pk = 0

    def __init__(self, pk, title, container=None, position_in_container=1):
        self.pk = pk
        self.title = title
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

    def get_phy_slug(self):
        """
        :return: the physical slug
        """
        return str(self.pk) + '_' + slugify(self.title)

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the extract.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        return os.path.join(self.container.get_path(relative=relative), self.get_phy_slug()) + '.md'

    def get_prod_path(self):
        """
        Get the physical path to the public version of a specific version of the extract.
        :return: physical path
        """
        return os.path.join(self.container.get_prod_path(), self.get_phy_slug()) + '.md.html'

    def get_text(self):
        if self.text:
            return get_blob(
                self.container.top_container().repository.commit(self.container.top_container().current_version).tree,
                self.text)

    def get_text_online(self):
        path = self.container.top_container().get_prod_path() + self.text + '.html'
        if os.path.exists(path):
            txt = open(path)
            txt_content = txt.read()
            txt.close()
            return txt_content.decode('utf-8')


class VersionedContent(Container):
    """
    This class is used to handle a specific version of a tutorial.

    It is created from the "manifest.json" file, and could dump information in it.

    For simplicity, it also contains DB information (but cannot modified them!), filled at the creation.
    """

    current_version = None
    repository = None

    description = ''
    type = ''
    licence = ''

    # Information from DB
    sha_draft = None
    sha_beta = None
    sha_public = None
    sha_validation = None
    is_beta = False
    is_validation = False
    is_public = False

    # TODO `load_dic()` provide more information, actually

    def __init__(self, current_version, pk, _type, title):
        Container.__init__(self, pk, title)
        self.current_version = current_version
        self.type = _type
        self.repository = Repo(self.get_path())
        # so read JSON ?

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """
        :return: the url to access the tutorial when offline
        """
        return reverse('zds.tutorialv2.views.view_tutorial', args=[self.pk, slugify(self.title)])

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return reverse('zds.tutorialv2.views.view_tutorial_online', args=[self.pk, slugify(self.title)])

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
        return reverse('zds.tutorialv2.views.modify_tutorial') + '?tutorial={0}'.format(self.pk)

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
            return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_path'], self.get_phy_slug())

    def get_prod_path(self):
        """
        Get the physical path to the public version of the content
        :return: physical path
        """
        return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_public_path'], self.get_phy_slug())

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

    These are two repositories : draft and online.
    """
    class Meta:
        verbose_name = 'Contenu'
        verbose_name_plural = 'Contenus'

    title = models.CharField('Titre', max_length=80)
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
        # TODO: for the logic with previous method, why not `in_public()` ?
        return (self.sha_public is not None) and (self.sha_public.strip() != '')

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

    def load_json_for_public(self, sha=None):
        """
        Fetch the public version of the JSON file for this content.
        :param sha: version
        :return: a dictionary containing the structure of the JSON file.
        """
        if sha is None:
            sha = self.sha_public
        repo = Repo(self.get_path())  # should be `get_prod_path()` !?!
        mantuto = get_blob(repo.commit(sha).tree, 'manifest.json')
        data = json_reader.loads(mantuto)
        if 'licence' in data:
            data['licence'] = Licence.objects.filter(code=data['licence']).first()
        return data
        # TODO: mix that with next function

    def load_dic(self, mandata, sha=None):
        # TODO should load JSON and store it in VersionedContent
        """
        Fill mandata with information from database model and add 'slug', 'is_beta', 'is_validation', 'is_on_line'.
        :param mandata: a dictionary from JSON file
        :param sha: current version, used to fill the `is_*` fields by comparison with the corresponding `sha_*`
        """
        # TODO: give it a more explicit name such as `insert_data_in_json()` ?

        fns = [
            'is_big', 'is_mini', 'have_markdown', 'have_html', 'have_pdf', 'have_epub', 'get_path', 'in_beta',
            'in_validation', 'on_line'
        ]

        attrs = [
            'pk', 'authors', 'subcategory', 'image', 'pubdate', 'update', 'source', 'sha_draft', 'sha_beta',
            'sha_validation', 'sha_public'
        ]

        # load functions and attributs in tree
        for fn in fns:
            mandata[fn] = getattr(self, fn)
        for attr in attrs:
            mandata[attr] = getattr(self, attr)

        # general information
        mandata['slug'] = slugify(mandata['title'])
        mandata['is_beta'] = self.in_beta() and self.sha_beta == sha
        mandata['is_validation'] = self.in_validation() and self.sha_validation == sha
        mandata['is_on_line'] = self.in_public() and self.sha_public == sha

        # url:
        mandata['get_absolute_url'] = reverse('zds.tutorialv2.views.view_tutorial', args=[self.pk, mandata['slug']])

        if self.in_beta():
            mandata['get_absolute_url_beta'] = reverse(
                'zds.tutorialv2.views.view_tutorial',
                args=[self.pk, mandata['slug']]
            ) + '?version=' + self.sha_beta

        else:
            mandata['get_absolute_url_beta'] = reverse(
                'zds.tutorialv2.views.view_tutorial',
                args=[self.pk, mandata['slug']]
            )

        mandata['get_absolute_url_online'] = reverse(
            'zds.tutorialv2.views.view_tutorial_online',
            args=[self.pk, mandata['slug']]
        )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)

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
        shutil.rmtree(self.get_path(), False)
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
