from django.db.models import CASCADE
from datetime import datetime
import contextlib

from zds.tutorialv2.models.mixins import TemplatableContentModelMixin, OnlineLinkableContentMixin
from zds import json_handler

from math import ceil
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.http import Http404
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_delete, post_delete, pre_save
from django.dispatch import receiver

from git import Repo, BadObject
from gitdb.exc import BadName
import os
from uuslug import uuslug

from elasticsearch_dsl import Mapping, Q as ES_Q
from elasticsearch_dsl.field import Text, Keyword, Date, Boolean

from zds.forum.models import Topic
from zds.gallery.models import Image, Gallery, UserGallery, GALLERY_WRITE
from zds.tutorialv2.managers import PublishedContentManager, PublishableContentManager
from zds.tutorialv2.models.versioned import NotAPublicVersion
from zds.tutorialv2.models import TYPE_CHOICES, STATUS_CHOICES, CONTENT_TYPES_REQUIRING_VALIDATION, PICK_OPERATIONS
from zds.tutorialv2.utils import get_content_from_json, BadManifestError
from zds.utils import get_current_user
from zds.utils.models import SubCategory, Licence, HelpWriting, Comment, Tag
from zds.searchv2.models import AbstractESDjangoIndexable, AbstractESIndexable, delete_document_in_elasticsearch, \
    ESIndexManager
from zds.utils.tutorials import get_blob
import logging


ALLOWED_TYPES = ['pdf', 'md', 'html', 'epub', 'zip', 'tex']
logger = logging.getLogger(__name__)


class PublishableContent(models.Model, TemplatableContentModelMixin):
    """A publishable content.

    A PublishableContent retains metadata about a content in database, such as

    - authors, description, source (if the content comes from another website), subcategory, tags and licence ;
    - Thumbnail and gallery ;
    - Creation, publication and update date ;
    - Public, beta, validation and draft sha, for versioning ;
    - Comment support ;
    - Type, which is either "ARTICLE" "TUTORIAL" or "OPINION"
    """
    class Meta:
        verbose_name = 'Contenu'
        verbose_name_plural = 'Contenus'

    content_type_attribute = 'type'
    title = models.CharField('Titre', max_length=80)
    slug = models.CharField('Slug', max_length=80)
    description = models.CharField('Description', max_length=200)
    source = models.CharField('Source', max_length=200, blank=True, null=True)
    authors = models.ManyToManyField(User, verbose_name='Auteurs', db_index=True)
    old_pk = models.IntegerField(db_index=True, default=0)
    subcategory = models.ManyToManyField(SubCategory,
                                         verbose_name='Sous-Catégorie',
                                         blank=True, db_index=True)

    tags = models.ManyToManyField(Tag, verbose_name='Tags du contenu', blank=True, db_index=True)
    # store the thumbnail for tutorial or article
    image = models.ForeignKey(Image,
                              verbose_name='Image du tutoriel',
                              blank=True, null=True,
                              on_delete=models.SET_NULL)

    # every publishable content has its own gallery to manage images
    gallery = models.ForeignKey(Gallery,
                                verbose_name="Galerie d'images",
                                blank=True, null=True, db_index=True)

    creation_date = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField('Date de publication',
                                   blank=True, null=True, db_index=True)
    update_date = models.DateTimeField('Date de mise à jour',
                                       blank=True, null=True)

    picked_date = models.DateTimeField('Date de mise en avant', db_index=True, blank=True, null=True, default=None)

    sha_public = models.CharField('Sha1 de la version publique',
                                  blank=True, null=True, max_length=80, db_index=True)
    sha_beta = models.CharField('Sha1 de la version beta publique',
                                blank=True, null=True, max_length=80, db_index=True)
    sha_validation = models.CharField('Sha1 de la version en validation',
                                      blank=True, null=True, max_length=80, db_index=True)
    sha_draft = models.CharField('Sha1 de la version de rédaction',
                                 blank=True, null=True, max_length=80, db_index=True)
    sha_picked = models.CharField('Sha1 de la version choisie (contenus publiés sans validation)',
                                  blank=True, null=True, max_length=80, db_index=True)
    beta_topic = models.ForeignKey(Topic, verbose_name='Sujet beta associé', default=None, blank=True, null=True)
    licence = models.ForeignKey(Licence,
                                verbose_name='Licence',
                                blank=True, null=True, db_index=True)
    # as of ZEP 12 this field is no longer the size but the type of content (article/tutorial/opinion)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    # zep03 field
    helps = models.ManyToManyField(HelpWriting, verbose_name='Aides', blank=True, db_index=True)

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

    must_reindex = models.BooleanField('Si le contenu doit-être ré-indexé', default=True)

    is_obsolete = models.BooleanField('Est obsolète', default=False)

    public_version = models.ForeignKey(
        'PublishedContent', verbose_name='Version publiée', blank=True, null=True, on_delete=models.SET_NULL)

    # FK to an opinion which has been converted to article. Useful to keep track of history and
    # to add a canonical link
    converted_to = models.ForeignKey(
        'self',
        verbose_name='Contenu promu',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='converted_from')

    objects = PublishableContentManager()

    def __str__(self):
        return self.title

    def update(self, **fields):
        """
        wrapper arround ``self.objects.update``

        :param fields: Fields to update
        :return: modified self
        """
        self.__class__.objects.filter(pk=self.pk).update(**fields)
        self.refresh_from_db(fields=list(fields.keys()))
        return self

    def save(self, *args, **kwargs):
        """
        Rewrite the `save()` function to handle slug uniqueness
        """
        if kwargs.pop('force_slug_update', True):
            self.slug = uuslug(self.title, instance=self, max_length=80)
        update_date = kwargs.pop('update_date', True)
        if update_date:
            self.update_date = datetime.now()
        super(PublishableContent, self).save(*args, **kwargs)

    def get_absolute_url_beta(self):
        """NOTE: it's better to use the version contained in `VersionedContent`, if possible !

        :return: absolute URL to the beta version the content
        :rtype: str
        """

        return reverse('content:beta-view', kwargs={'pk': self.pk, 'slug': self.slug})

    def get_absolute_url_online(self):
        """NOTE: it's better to use the version contained in `VersionedContent`, if possible !

        :return:  absolute URL to the public version the content, if `self.public_version` is defined
        :rtype: str
        """

        if self.public_version:
            return self.public_version.get_absolute_url_online()

        return ''

    def get_absolute_contact_url(self, title='Collaboration'):
        """ Get url to send a new PM for collaboration

        :param title: what is going to be in the title of the PM before the name of the content
        :type title: str
        :return: url to the PM creation form
        :rtype: str
        """
        get = '?' + urlencode({'title': '{} - {}'.format(title, self.title)})

        for author in self.authors.all():
            get += '&' + urlencode({'username': author.username})

        return reverse('mp-new') + get

    def get_repo_path(self, relative=False):
        """Get the path to the tutorial repository

        :param relative: if ``True``, the path will be relative, absolute otherwise.
        :return: physical path
        :rtype: str
        """
        if relative:
            return ''
        else:
            # get the full path (with tutorial/article before it)
            return os.path.join(settings.ZDS_APP['content']['repo_private_path'], self.slug)

    def ensure_author_gallery(self):
        """
        ensure all authors subscribe to gallery
        """
        author_set = UserGallery.objects.filter(user__in=list(self.authors.all()), gallery=self.gallery)\
            .values_list('user__pk', flat=True)
        for author in self.authors.all():
            if author.pk in author_set:
                continue
            user_gallery = UserGallery()
            user_gallery.gallery = self.gallery
            user_gallery.mode = GALLERY_WRITE  # write mode
            user_gallery.user = author
            user_gallery.save()

    def in_beta(self):
        """A tutorial is not in beta if sha_beta is ``None`` or empty


        :return: ``True`` if the tutorial is in beta, ``False`` otherwise
        :rtype: bool
        """
        return (self.sha_beta is not None) and (self.sha_beta.strip() != '')

    def in_validation(self):
        """A tutorial is not in validation if sha_validation is ``None`` or empty

        :return: ``True`` if the tutorial is in validation, ``False`` otherwise
        :rtype: bool
        """
        return (self.sha_validation is not None) and (self.sha_validation.strip() != '')

    def in_drafting(self):
        """A tutorial is not in draft if sha_draft is ``None`` or empty

        :return: ``True`` if the tutorial is in draft, ``False`` otherwise
        :rtype: bool
        """
        return (self.sha_draft is not None) and (self.sha_draft.strip() != '')

    def in_public(self):
        """A tutorial is not in on line if sha_public is ``None`` or empty

        :return: ``True`` if the tutorial is on line, ``False`` otherwise
        :rtype: bool
        """
        return (self.sha_public is not None) and (self.sha_public.strip() != '')

    def is_beta(self, sha):
        """Is this version of the content the beta version ?

        :param sha: version
        :return: ``True`` if the tutorial is in beta, ``False`` otherwise
        :rtype: bool
        """
        return self.in_beta() and sha == self.sha_beta

    def is_validation(self, sha):
        """Is this version of the content the validation version ?

        :param sha: version
        :return: ``True`` if the tutorial is in validation, ``False`` otherwise
        :rtype: bool
        """
        return self.in_validation() and sha == self.sha_validation

    def is_public(self, sha):
        """Is this version of the content the published version ?

        :param sha: version
        :return: ``True`` if the tutorial is in public, ``False`` otherwise
        :rtype: bool
        """
        return self.in_public() and sha == self.sha_public

    def is_permanently_unpublished(self):
        """Is this content permanently unpublished by a moderator ?"""

        return PickListOperation.objects.filter(content=self, operation='REMOVE_PUB', is_effective=True).exists()

    def load_version_or_404(self, sha=None, public=None):
        """Using git, load a specific version of the content. if `sha` is `None`, the draft/public version is used (if
        `public` is `True`).

        :param sha: version
        :param public: if set with the right object, return the public version
        :type public: PublishedContent
        :raise Http404: if sha is not None and related version could not be found
        :return: the versioned content
        :rtype: zds.tutorialv2.models.versioned.ViersionedContent
        """
        try:
            return self.load_version(sha, public)
        except (BadObject, BadName, OSError) as error:
            raise Http404(
                'Le code sha existe mais la version demandée ne peut pas être trouvée à cause de {}:{}'.format(
                    type(error), str(error)))

    def load_version(self, sha=None, public=None):
        """Using git, load a specific version of the content. if ``sha`` is ``None``,
        the draft/public version is used (if ``public`` is ``True``).

        .. attention::

            for practical reason, the returned object is filled with information from DB.

        :param sha: version
        :param public: if set with the right object, return the public version
        :type public: PublishedContent
        :raise BadObject: if sha is not None and related version could not be found
        :raise OSError: if the path to the repository is wrong
        :raise NotAPublicVersion: if the sha does not correspond to a public version
        :return: the versioned content
        :rtype: zds.tutorialv2.models.versioned.VersionedContent
        """

        # load the good manifest.json
        if sha is None:
            if not public:
                sha = self.sha_draft
            else:
                sha = self.sha_public
        max_title_length = PublishableContent._meta.get_field('title').max_length
        if public and isinstance(public, PublishedContent):  # use the public (altered and not versioned) repository
            path = public.get_prod_path()
            slug = public.content_public_slug

            if not os.path.isdir(path):
                raise OSError(path)

            if sha != public.sha_public:
                raise NotAPublicVersion

            with open(os.path.join(path, 'manifest.json'), 'r', encoding='utf-8') as manifest:
                json = json_handler.loads(manifest.read())
                versioned = get_content_from_json(
                    json,
                    public.sha_public,
                    slug,
                    public=True,
                    max_title_len=max_title_length,
                    hint_licence=self.licence,
                )

        else:  # draft version, use the repository (slower, but allows manipulation)
            path = self.get_repo_path()

            if not os.path.isdir(path):
                raise OSError(path)

            repo = Repo(path)
            data = get_blob(repo.commit(sha).tree, 'manifest.json')
            try:
                json = json_handler.loads(data)
            except ValueError:
                raise BadManifestError(
                    _('Une erreur est survenue lors de la lecture du manifest.json, est-ce du JSON ?'))

            versioned = get_content_from_json(json, sha, self.slug, max_title_len=max_title_length)

        self.insert_data_in_versioned(versioned)
        return versioned

    def insert_data_in_versioned(self, versioned):
        """Insert some additional data from database in a VersionedContent

        :param versioned: the VersionedContent to fill
        """

        attrs = [
            'pk', 'authors', 'subcategory', 'image', 'creation_date', 'pubdate', 'update_date', 'source',
            'sha_draft', 'sha_beta', 'sha_validation', 'sha_public', 'tags', 'sha_picked', 'converted_to',
            'type'
        ]

        fns = [
            'in_beta', 'in_validation', 'in_public',
            'get_absolute_contact_url', 'get_note_count', 'antispam'
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
        """Count all the reactions to this content. Warning, if you did not pre process this number, \
        a query will be sent

        :return: number of notes in the tutorial.
        :rtype: int
        """
        try:
            return self.count_note
        except AttributeError:
            self.count_note = ContentReaction.objects.filter(related_content__pk=self.pk).count()
            return self.count_note

    def get_last_note(self):
        """
        :return: the last answer in the thread, if any.
        :rtype: ContentReaction|None
        """
        return ContentReaction.objects.all()\
            .select_related('related_content')\
            .select_related('related_content__public_version')\
            .filter(related_content__pk=self.pk)\
            .order_by('-pubdate')\
            .first()

    def first_note(self):
        """
        :return: the first post of a topic, written by topic's author, if any.
        :rtype: ContentReaction
        """
        return ContentReaction.objects\
            .select_related('related_content')\
            .select_related('related_content__public_version')\
            .filter(related_content=self)\
            .order_by('pubdate')\
            .first()

    def last_read_note(self):
        """
        :return: the last post the user has read.
        :rtype: ContentReaction
        """
        user = get_current_user()

        if user and user.is_authenticated():
            try:
                read = ContentRead.objects\
                    .select_related('note')\
                    .select_related('note__related_content')\
                    .select_related('note__related_content__public_version')\
                    .filter(content=self, user__pk=user.pk)\
                    .latest('note__pubdate')
                if read is not None and read.note:  # one case can show a read without note : the author has just
                    # published his content and one comment has been posted by someone else.
                    return read.note

            except ContentRead.DoesNotExist:
                pass

        return self.first_note()

    def first_unread_note(self, user=None):
        """
        :return: Return the first note the user has unread.
        :rtype: ContentReaction
        """
        if user is None:
            user = get_current_user()

        if user and user.is_authenticated():
            try:
                read = ContentRead.objects\
                    .filter(content=self, user__pk=user.pk)\
                    .latest('note__pubdate')

                if read and read.note:
                    last_note = read.note

                    next_note = ContentReaction.objects\
                        .select_related('related_content')\
                        .select_related('related_content__public_version')\
                        .filter(
                            related_content__pk=self.pk,
                            pk__gt=last_note.pk)\
                        .select_related('author').first()

                    if next_note:
                        return next_note
                    else:
                        return last_note

            except ContentRead.DoesNotExist:
                pass

        return self.first_note()

    def antispam(self, user=None):
        """Check if the user is allowed to post in an tutorial according to the SPAM_LIMIT_SECONDS value.

        :param user: the user to check antispam. If ``None``, current user is used.
        :return: ``True`` if the user is not able to note (the elapsed time is not enough), ``False`` otherwise.
        :rtype: bool
        """
        if user is None:
            user = get_current_user()

        if user and user.is_authenticated():
            last_user_notes = ContentReaction.objects\
                .filter(related_content=self)\
                .filter(author=user.pk)\
                .order_by('-position')

            if last_user_notes and last_user_notes[0] == self.last_note:
                last_user_note = last_user_notes[0]
                t = datetime.now() - last_user_note.pubdate
                if t.total_seconds() < settings.ZDS_APP['forum']['spam_limit_seconds']:
                    return True

    def repo_delete(self):
        """
        Delete the entities and their filesystem counterparts
        """
        if os.path.exists(self.get_repo_path()):
            shutil.rmtree(self.get_repo_path(), False)
        if self.in_public() and self.public_version:
            if os.path.exists(self.public_version.get_prod_path()):
                shutil.rmtree(self.public_version.get_prod_path())

        Validation.objects.filter(content=self).delete()

    def add_tags(self, tag_collection):
        """
        Add all tags contained in `tag_collection` to this content.
        If a tag is unknown, it is added to the system.
        :param tag_collection: A collection of tags.
        :type tag_collection: list
        """
        for tag in tag_collection:
            try:
                current_tag, created = Tag.objects.get_or_create(title=tag.lower().strip())
                self.tags.add(current_tag)
            except ValueError as e:
                logger.warning(e)

        self.save()

    def requires_validation(self):
        """
        Check if content required a validation before publication.
        Used to check if JsFiddle is available too.

        :return: Whether validation is required before publication.
        :rtype: bool
        """
        return self.type in CONTENT_TYPES_REQUIRING_VALIDATION


@receiver(pre_delete, sender=PublishableContent)
def delete_repo(sender, instance, **kwargs):
    """catch the pre_delete signal to ensure the deletion of the repository if a PublishableContent is deleted"""
    instance.repo_delete()


@receiver(post_delete, sender=PublishableContent)
def delete_gallery(sender, instance, **kwargs):
    """catch the post_delete signal to ensure the deletion of the gallery (otherwise, you generate a loop)"""
    if instance.gallery:
        instance.gallery.delete()


class PublishedContent(AbstractESDjangoIndexable, TemplatableContentModelMixin, OnlineLinkableContentMixin):
    """A class that contains information on the published version of a content.

    Used for quick url resolution, quick listing, and to know where the public version of the files are.

    Linked to a ``PublishableContent`` for the rest. Don't forget to add a ``.prefetch_related('content')`` !!
    """

    objects_per_batch = 25

    class Meta:
        verbose_name = 'Contenu publié'
        verbose_name_plural = 'Contenus publiés'

    content = models.ForeignKey(PublishableContent, verbose_name='Contenu')

    content_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True, verbose_name='Type de contenu')
    content_public_slug = models.CharField('Slug du contenu publié', max_length=80)
    content_pk = models.IntegerField('Pk du contenu publié', db_index=True)

    publication_date = models.DateTimeField('Date de publication', db_index=True, blank=True, null=True)
    update_date = models.DateTimeField('Date de mise à jour', db_index=True, blank=True, null=True, default=None)
    sha_public = models.CharField('Sha1 de la version publiée', blank=True, null=True, max_length=80, db_index=True)
    char_count = models.IntegerField(default=None, null=True, verbose_name=b'Nombre de lettres du contenu', blank=True)

    must_redirect = models.BooleanField(
        'Redirection vers  une version plus récente', blank=True, db_index=True, default=False)

    authors = models.ManyToManyField(User, verbose_name='Auteurs', db_index=True)

    objects = PublishedContentManager()
    versioned_model = None

    # sizes contain a python dict (as a string in database) with all information about file sizes
    sizes = models.CharField('Tailles des fichiers téléchargeables', max_length=512, default='{}')

    @staticmethod
    def get_slug_from_file_path(file_path):
        return os.path.splitext(os.path.split(file_path)[1])[0]

    def __str__(self):
        return _('Version publique de "{}"').format(self.content.title)

    def title(self):
        if self.versioned_model:
            return self.versioned_model.title
        else:
            return self.load_public_version().title

    def description(self):
        if self.versioned_model:
            return self.versioned_model.description
        else:
            return self.load_public_version().description

    def get_prod_path(self, relative=False):
        if not relative:
            return os.path.join(settings.ZDS_APP['content']['repo_public_path'], self.content_public_slug)
        else:
            return ''

    def load_public_version_or_404(self):
        """
        :return: the public content
        :rtype: zds.tutorialv2.models.database.PublicContent
        :raise Http404: if the version is not available
        """
        with contextlib.suppress(AttributeError):
            self.content.count_note = self.count_note

        self.versioned_model = self.content.load_version_or_404(sha=self.sha_public, public=self)
        return self.versioned_model

    def load_public_version(self):
        """
        :rtype: zds.tutorialv2.models.database.PublicContent
        :return: the public content
        """
        with contextlib.suppress(AttributeError):
            self.content.count_note = self.count_note

        self.versioned_model = self.content.load_version(sha=self.sha_public, public=self)
        return self.versioned_model

    def get_extra_contents_directory(self):
        """
        :return: path to all the 'extra contents'
        :rtype: str
        """
        return os.path.join(self.get_prod_path(), settings.ZDS_APP['content']['extra_contents_dirname'])

    def has_type(self, type_):
        """check if a given extra content exists

        :return: ``True`` if the file exists, ``False`` otherwhise
        :rtype: bool
        """

        if type_ in ALLOWED_TYPES:
            return os.path.isfile(
                os.path.join(self.get_extra_contents_directory(), self.content_public_slug + '.' + type_))

        return False

    def has_md(self):
        """Check if the flat markdown version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type('md')

    def has_html(self):
        """Check if the html version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type('html')

    def has_pdf(self):
        """Check if the pdf version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type('pdf')

    def has_epub(self):
        """Check if the standard epub version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type('epub')

    def has_zip(self):
        """Check if the standard zip version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type('zip')

    def get_size_file_type(self, type_):
        """
        Get the size of a given extra content.
        Is the size is not in database we get it and store it for next time.

        :return: size of file
        :rtype: int
        """
        if type_ in ALLOWED_TYPES:
            sizes = eval(str(self.sizes))
            try:
                size = sizes[type_]
            except KeyError:
                # if size is not in database we store it
                sizes[type_] = os.path.getsize(os.path.join(
                    self.get_extra_contents_directory(), self.content_public_slug + '.' + type_))
                self.sizes = sizes
                self.save()
                size = sizes[type_]
            return size
        return None

    def get_size_md(self):
        """Get the size of md

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type('md')

    def get_size_html(self):
        """Get the size of html

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type('html')

    def get_size_pdf(self):
        """Get the size of pdf

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type('pdf')

    def get_size_epub(self):
        """Get the size of epub

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type('epub')

    def get_size_zip(self):
        """Get the size of zip

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type('zip')

    def get_absolute_url_to_extra_content(self, type_):
        """Get the url that point to the extra content the user may want to download

        :param type_: the type inside allowed_type
        :type type_: str
        :return: URL to a given extra content (note that no check for existence is done)
        :rtype: str
        """

        if type_ in ALLOWED_TYPES:
            reversed_ = self.content_type.lower()
            return reverse(
                reversed_ + ':download-' + type_, kwargs={'pk': self.content_pk, 'slug': self.content_public_slug})
        return ''

    def get_absolute_url_md(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('md')``

        :return: URL to the full markdown version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content('md')

    def get_absolute_url_html(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('html')``

        :return: URL to the HTML version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content('html')

    def get_absolute_url_pdf(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('pdf')``

        :return: URL to the PDF version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content('pdf')

    def get_absolute_url_epub(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('epub')``

        :return: URL to the epub version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content('epub')

    def get_absolute_url_zip(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('zip')``

        :return: URL to the zip archive of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content('zip')

    def get_last_action_date(self):
        return self.update_date or self.publication_date

    def get_char_count(self, md_file_path=None):
        """ Compute the number of letters for a given content

        :param md_file_path: use another file to compute the number of letter rather than the default one.
        :type md_file_path: str
        :return: Number of letters in the md file
        :rtype: int
        """

        if not md_file_path:
            md_file_path = os.path.join(self.get_extra_contents_directory(), self.content_public_slug + '.md')

        try:
            with open(md_file_path, 'rb') as md_file:
                content = md_file.read().decode('utf-8')
            current_content = PublishedContent.objects.filter(content_pk=self.content_pk, must_redirect=False).first()
            if current_content:
                return len(content)
        except OSError as e:
            logger.warning('could not get file %s to compute nb letters (error=%s)', md_file_path, e)

    @classmethod
    def get_es_mapping(cls):
        mapping = Mapping(cls.get_es_document_type())

        mapping.field('content_pk', 'integer')
        mapping.field('publication_date', Date())
        mapping.field('content_type', Keyword())

        # not from PublishedContent directly:
        mapping.field('title', Text(boost=1.5))
        mapping.field('description', Text(boost=1.5))
        mapping.field('tags', Text(boost=2.0))
        mapping.field('categories', Keyword(boost=1.5))
        mapping.field('subcategories', Keyword(boost=1.5))
        mapping.field('text', Text())  # for article and mini-tuto, text is directly included into the main object
        mapping.field('has_chapters', Boolean())  # ... otherwise, it is written
        mapping.field('picked', Boolean())

        # not indexed:
        mapping.field('get_absolute_url_online', Keyword(index=False))
        mapping.field('thumbnail', Keyword(index=False))

        return mapping

    @classmethod
    def get_es_django_indexable(cls, force_reindexing=False):
        """Overridden to remove must_redirect=True (and prefetch stuffs).
        """

        q = super(PublishedContent, cls).get_es_django_indexable(force_reindexing)
        return q.prefetch_related('content')\
            .prefetch_related('content__tags')\
            .prefetch_related('content__subcategory')\
            .select_related('content__image')\
            .filter(must_redirect=False)

    @classmethod
    def get_es_indexable(cls, force_reindexing=False):
        """Overridden to also include chapters
        """

        index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

        # fetch initial batch
        last_pk = 0
        objects_source = super(PublishedContent, cls).get_es_indexable(force_reindexing)
        objects = list(objects_source.filter(pk__gt=last_pk)[:PublishedContent.objects_per_batch])

        while objects:
            chapters = []

            for content in objects:
                versioned = content.load_public_version()

                # chapters are only indexed for middle and big tuto
                if versioned.has_sub_containers():

                    # delete possible previous chapters
                    if content.es_already_indexed:
                        index_manager.delete_by_query(
                            FakeChapter.get_es_document_type(), ES_Q('match', _routing=content.es_id))

                    # (re)index the new one(s)
                    for chapter in versioned.get_list_of_chapters():
                        chapters.append(FakeChapter(chapter, versioned, content.es_id))

            if chapters:
                # since we want to return at most PublishedContent.objects_per_batch items
                # we have to split further
                while chapters:
                    yield chapters[:PublishedContent.objects_per_batch]
                    chapters = chapters[PublishedContent.objects_per_batch:]
            if objects:
                yield objects

            # fetch next batch
            last_pk = objects[-1].pk
            objects = list(objects_source.filter(pk__gt=last_pk)[:PublishedContent.objects_per_batch])

    def get_es_document_source(self, excluded_fields=None):
        """Overridden to handle the fact that most information are versioned
        """

        excluded_fields = excluded_fields or []
        excluded_fields.extend(['title', 'description', 'tags', 'categories', 'text', 'thumbnail', 'picked'])

        data = super(PublishedContent, self).get_es_document_source(excluded_fields=excluded_fields)

        # fetch versioned information
        versioned = self.load_public_version()

        data['title'] = versioned.title
        data['description'] = versioned.description
        data['tags'] = [tag.title for tag in versioned.tags.all()]

        if self.content.image:
            data['thumbnail'] = self.content.image.physical['content_thumb'].url

        categories = []
        subcategories = []
        for subcategory in versioned.subcategory.all():
            parent_category = subcategory.get_parent_category()
            if subcategory.slug not in subcategories:
                subcategories.append(subcategory.slug)
            if parent_category and parent_category.slug not in categories:
                categories.append(parent_category.slug)

        data['categories'] = categories
        data['subcategories'] = subcategories

        if versioned.has_extracts():
            data['text'] = versioned.get_content_online()
            data['has_chapters'] = False
        else:
            data['has_chapters'] = True

        data['picked'] = False

        if self.content_type == 'OPINION' and self.content.sha_picked is not None:
            data['picked'] = True

        return data


@receiver(pre_delete, sender=PublishedContent)
def delete_published_content_in_elasticsearch(sender, instance, **kwargs):
    """Catch the pre_delete signal to ensure the deletion in ES. Also, handle the deletion of the corresponding
    chapters.
    """

    index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    if index_manager.index_exists:
        index_manager.delete_by_query(FakeChapter.get_es_document_type(), ES_Q('match', _routing=instance.es_id))

    return delete_document_in_elasticsearch(instance)


@receiver(pre_save, sender=PublishedContent)
def delete_published_content_in_elasticsearch_if_set_to_redirect(sender, instance, **kwargs):
    """If the slug of the content changes, the ``must_redirect`` field is set to ``True`` and a new
    PublishedContnent is created. To avoid duplicates, the previous ones must be removed from ES.
    """

    try:
        obj = PublishedContent.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass  # nothing to worry about
    else:
        if not obj.must_redirect and instance.must_redirect:
            delete_published_content_in_elasticsearch(sender, instance, **kwargs)


class FakeChapter(AbstractESIndexable):
    """A simple class that is used by ES to index chapters, constructed from the containers.

    In mapping, this class defines PublishedContent as its parent. Also, indexing is done by the parent.

    Note that this class is only indexable, not updatable, since it does not maintain value of ``es_already_indexed``
    """

    parent_model = PublishedContent
    text = ''
    title = ''
    parent_id = ''
    get_absolute_url_online = ''
    parent_title = ''
    parent_get_absolute_url_online = ''
    parent_publication_date = ''
    thumbnail = ''
    categories = None
    subcategories = None

    def __init__(self, chapter, main_container, parent_id):
        self.title = chapter.title
        self.text = chapter.get_content_online()
        self.parent_id = parent_id
        self.get_absolute_url_online = chapter.get_absolute_url_online()

        self.es_id = main_container.slug + '__' + chapter.slug  # both slugs are unique by design, so id remains unique

        self.parent_title = main_container.title
        self.parent_get_absolute_url_online = main_container.get_absolute_url_online()
        self.parent_publication_date = main_container.pubdate

        if main_container.image:
            self.thumbnail = main_container.image.physical['content_thumb'].url

        self.categories = []
        self.subcategories = []
        for subcategory in main_container.subcategory.all():
            parent_category = subcategory.get_parent_category()
            if subcategory.slug not in self.subcategories:
                self.subcategories.append(subcategory.slug)
            if parent_category and parent_category.slug not in self.categories:
                self.categories.append(parent_category.slug)

    @classmethod
    def get_es_document_type(cls):
        return 'chapter'

    @classmethod
    def get_es_mapping(self):
        """Define mapping and parenting
        """

        mapping = Mapping(self.get_es_document_type())
        mapping.meta('parent', type='publishedcontent')

        mapping.field('title', Text(boost=1.5))
        mapping.field('text', Text())
        mapping.field('categories', Keyword(boost=1.5))
        mapping.field('subcategories', Keyword(boost=1.5))

        # not indexed:
        mapping.field('get_absolute_url_online', Keyword(index=False))
        mapping.field('parent_title', Text(index=False))
        mapping.field('parent_get_absolute_url_online', Keyword(index=False))
        mapping.field('parent_publication_date', Date(index=False))
        mapping.field('thumbnail', Keyword(index=False))

        return mapping

    def get_es_document_as_bulk_action(self, index, action='index'):
        """Overridden to handle parenting between chapter and PublishedContent
        """

        document = super(FakeChapter, self).get_es_document_as_bulk_action(index, action)
        document['_parent'] = self.parent_id
        return document


class ContentReaction(Comment):
    """
    A comment written by any user about a PublishableContent they just read.
    """
    class Meta:
        verbose_name = 'note sur un contenu'
        verbose_name_plural = 'notes sur un contenu'

    related_content = models.ForeignKey(PublishableContent, verbose_name='Contenu',
                                        related_name='related_content_note', db_index=True)

    def __str__(self):
        return "<Réaction pour '{0}', #{1}>".format(self.related_content, self.pk)

    def get_absolute_url(self):
        """Find the url to the reaction

        :return: the url of the comment
        :rtype: str
        """
        page = int(ceil(float(self.position) / settings.ZDS_APP['content']['notes_per_page']))
        return '{0}?page={1}#p{2}'.format(self.related_content.get_absolute_url_online(), page, self.pk)

    def get_notification_title(self):
        return self.related_content.title


class ContentRead(models.Model):
    """
    Small model which keeps track of the user viewing tutorials.

    It remembers the PublishableContent they read and what was the last Note at that time.
    """
    class Meta:
        verbose_name = 'Contenu lu'
        verbose_name_plural = 'Contenu lus'

    content = models.ForeignKey(PublishableContent, db_index=True)
    note = models.ForeignKey(ContentReaction, db_index=True, null=True)
    user = models.ForeignKey(User, related_name='content_notes_read', db_index=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Save this model but check that if we have not a related note it is because the user is content author.
        """
        if self.user not in self.content.authors.all() and self.note is None:
            raise ValueError(_("La note doit exister ou l'utilisateur doit être l'un des auteurs."))

        return super(ContentRead, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return '<Contenu "{}" lu par {}, #{}>'.format(self.content, self.user, self.note.pk)


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
    date_proposition = models.DateTimeField('Date de proposition', db_index=True, null=True, blank=True)
    comment_authors = models.TextField("Commentaire de l'auteur", null=True, blank=True)
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

    def __str__(self):
        return _('Validation de « {} »').format(self.content.title)

    def is_pending(self):
        """Check if the validation is pending

        :return: ``True`` if status is pending, ``False`` otherwise
        :rtype: bool
        """
        return self.status == 'PENDING'

    def is_pending_valid(self):
        """Check if the validation is pending (but there is a validator)

        :return: ``True`` if status is pending/valid, ``False`` otherwise
        :rtype: bool
        """
        return self.status == 'PENDING_V'

    def is_accept(self):
        """Check if the content is accepted

        :return: ``True`` if status is accepted, ``False`` otherwise
        :rtype: bool
        """
        return self.status == 'ACCEPT'

    def is_reject(self):
        """Check if the content is rejected

        :return: ``True`` if status is rejected, ``False`` otherwise
        :rtype: bool
        """
        return self.status == 'REJECT'

    def is_cancel(self):
        """Check if the content is canceled

        :return: ``True`` if status is canceled, ``False`` otherwise
        :rtype: bool
        """
        return self.status == 'CANCEL'


class PickListOperation(models.Model):
    class Meta:
        verbose_name = "Choix d'un billet"
        verbose_name_plural = 'Choix des billets'

    content = models.ForeignKey(PublishableContent, null=False, blank=False,
                                verbose_name='Contenu proposé', db_index=True)
    operation = models.CharField(null=False, blank=False, db_index=True, max_length=len('REMOVE_PUB'),
                                 choices=PICK_OPERATIONS)
    operation_date = models.DateTimeField(null=False, db_index=True, verbose_name="Date de l'opération")
    version = models.CharField(null=False, blank=False, max_length=128, verbose_name='Version du billet concernée')
    staff_user = models.ForeignKey(User, null=False, blank=False, on_delete=CASCADE,
                                   verbose_name='Modérateur', related_name='pick_operations')
    canceler_user = models.ForeignKey(User, null=True, blank=True, on_delete=CASCADE,
                                      verbose_name='Modérateur qui a annulé la décision',
                                      related_name='canceled_pick_operations')
    is_effective = models.BooleanField(verbose_name='Choix actif', default=True)

    def __str__(self):
        return '{} : {}'.format(self.get_operation_display(), self.content)

    def cancel(self, canceler, autosave=True):
        """
        Cancel a decision
        :param canceler: staff user
        :param autosave: if ``True`` saves the modification
        """
        self.is_effective = False
        self.canceler_user = canceler
        if autosave:
            self.save()

    def save(self, **kwargs):
        if self.content is not None and self.content.type == 'OPINION':
            return super(PickListOperation, self).save(**kwargs)
        raise ValueError('Content cannot be null or something else than opinion.', self.content)


@receiver(models.signals.pre_delete, sender=User)
def transfer_paternity_receiver(sender, instance, **kwargs):
    """
    transfer paternity to external user on user deletion
    """
    external = sender.objects.get(username=settings.ZDS_APP['member']['external_account'])
    PublishableContent.objects.transfer_paternity(instance, external, UserGallery)
    PublishedContent.objects.transfer_paternity(instance, external)

import zds.tutorialv2.receivers  # noqa
