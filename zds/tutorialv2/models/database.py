import contextlib
import logging
import os
import shutil
from datetime import datetime
from math import ceil
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.http import Http404
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from git import BadObject, Repo
from gitdb.exc import BadName

from zds import json_handler
from zds.forum.models import Topic
from zds.gallery.models import GALLERY_WRITE, Gallery, Image, UserGallery
from zds.member.utils import get_external_account
from zds.mp.models import PrivateTopic
from zds.search.models import AbstractSearchIndexable, AbstractSearchIndexableModel
from zds.search.utils import SearchFilter, SearchIndexManager, clean_html, date_to_timestamp_int
from zds.tutorialv2.managers import PublishableContentManager, PublishedContentManager, ReactionManager
from zds.tutorialv2.models import (
    CONTENT_TYPES_BETA,
    CONTENT_TYPES_REQUIRING_VALIDATION,
    PICK_OPERATIONS,
    STATUS_CHOICES,
    TYPE_CHOICES,
)
from zds.tutorialv2.models.goals import Goal
from zds.tutorialv2.models.help_requests import HelpWriting
from zds.tutorialv2.models.labels import Label
from zds.tutorialv2.models.mixins import OnlineLinkableContentMixin, TemplatableContentModelMixin
from zds.tutorialv2.models.versioned import NotAPublicVersion
from zds.tutorialv2.utils import BadManifestError, get_blob, get_content_from_json
from zds.utils import get_current_user
from zds.utils.models import Category, Comment, Licence, SubCategory, Tag
from zds.utils.templatetags.emarkdown import render_markdown_stats
from zds.utils.uuslug_wrapper import uuslug

ALLOWED_TYPES = ["pdf", "md", "epub", "zip", "tex"]
logger = logging.getLogger(__name__)


class PublishableContent(models.Model, TemplatableContentModelMixin):
    """A publishable content.

    A PublishableContent retains metadata about a content in database, such as

    - authors, description, source (if the content comes from another website), subcategory, tags and licence ;
    - Thumbnail and gallery ;
    - Creation, publication and update date ;
    - Public, beta, validation and draft sha, for versioning ;
    - Comment support ;
    - Type, which is either ``'ARTICLE'``, ``'TUTORIAL'`` or ``'OPINION'``
    """

    class Meta:
        verbose_name = "Contenu"
        verbose_name_plural = "Contenus"

    content_type_attribute = "type"
    title = models.CharField("Titre", max_length=80)
    slug = models.CharField("Slug", max_length=80)
    description = models.CharField("Description", max_length=200)
    source = models.URLField("Source", max_length=200, blank=True, null=True)
    authors = models.ManyToManyField(User, verbose_name="Auteurs", db_index=True)
    old_pk = models.IntegerField(db_index=True, default=0)
    subcategory = models.ManyToManyField(SubCategory, verbose_name="Sous-Catégorie", blank=True, db_index=True)
    tags = models.ManyToManyField(Tag, verbose_name="Tags du contenu", blank=True, db_index=True)
    goals = models.ManyToManyField(
        Goal, verbose_name="Objectifs du contenu", blank=True, db_index=True, related_name="contents"
    )

    labels = models.ManyToManyField(
        Label, verbose_name="Labels du contenu", blank=True, db_index=True, related_name="contents"
    )

    # store the thumbnail for tutorial or article
    image = models.ForeignKey(Image, verbose_name="Image du tutoriel", blank=True, null=True, on_delete=models.SET_NULL)

    # every publishable content has its own gallery to manage images
    gallery = models.ForeignKey(
        Gallery, verbose_name="Galerie d'images", blank=True, null=True, db_index=True, on_delete=models.SET_NULL
    )

    creation_date = models.DateTimeField("Date de création")
    pubdate = models.DateTimeField("Date de publication", blank=True, null=True, db_index=True)
    update_date = models.DateTimeField("Date de mise à jour", blank=True, null=True)

    picked_date = models.DateTimeField("Date de mise en avant", db_index=True, blank=True, null=True, default=None)

    sha_public = models.CharField("Sha1 de la version publique", blank=True, null=True, max_length=80, db_index=True)
    sha_beta = models.CharField("Sha1 de la version beta publique", blank=True, null=True, max_length=80, db_index=True)
    sha_validation = models.CharField(
        "Sha1 de la version en validation", blank=True, null=True, max_length=80, db_index=True
    )
    sha_draft = models.CharField("Sha1 de la version de rédaction", blank=True, null=True, max_length=80, db_index=True)
    sha_picked = models.CharField(
        "Sha1 de la version choisie (contenus publiés sans validation)",
        blank=True,
        null=True,
        max_length=80,
        db_index=True,
    )
    beta_topic = models.ForeignKey(
        Topic, verbose_name="Sujet beta associé", default=None, blank=True, null=True, on_delete=models.SET_NULL
    )
    validation_private_message = models.ForeignKey(
        PrivateTopic,
        verbose_name="Message de suivi staff",
        default=None,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    licence = models.ForeignKey(
        Licence, verbose_name="Licence", blank=True, null=True, db_index=True, on_delete=models.SET_NULL
    )
    # as of ZEP 12 this field is no longer the size but the type of content (article/tutorial/opinion)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    # zep03 field
    helps = models.ManyToManyField(HelpWriting, verbose_name="Aides", blank=True, db_index=True)

    relative_images_path = models.CharField("chemin relatif images", blank=True, null=True, max_length=200)

    last_note = models.ForeignKey(
        "ContentReaction",
        blank=True,
        null=True,
        related_name="last_note",
        verbose_name="Derniere note",
        on_delete=models.SET_NULL,
    )
    is_locked = models.BooleanField("Est verrouillé", default=False)
    js_support = models.BooleanField("Support du Javascript", default=False)

    is_obsolete = models.BooleanField("Est obsolète", default=False)

    public_version = models.ForeignKey(
        "PublishedContent", verbose_name="Version publiée", blank=True, null=True, on_delete=models.SET_NULL
    )

    # FK to an opinion which has been converted to article. Useful to keep track of history and
    # to add a canonical link
    converted_to = models.ForeignKey(
        "self",
        verbose_name="Contenu promu",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="converted_from",
    )

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

    def save(self, *args, force_slug_update=False, update_date=True, **kwargs):
        """
        Rewrite the ``save()``  function to handle slug uniqueness

        :param update_date: if ``True`` will assign "update_date" property to now
        :param force_slug_update: if ``True`` will try to update the slug
        """
        if self.slug == "" or force_slug_update:
            self.slug = uuslug(self.title, instance=self, max_length=80)
        if update_date:
            self.update_date = datetime.now()
        if self.public_version:
            # This will probably triggers more reindexing than actually
            # required (for instance, when updating an attribute that is not
            # indexed), but it's definitely simpler than tracking which
            # attributes are changed.
            self.public_version.search_engine_requires_index = True
            self.public_version.save()
        super().save(*args, **kwargs)

    def get_absolute_url_beta(self):
        """NOTE: it's better to use the version contained in `VersionedContent`, if possible !

        :return: absolute URL to the beta version the content
        :rtype: str
        """

        return reverse("content:beta-view", kwargs={"pk": self.pk, "slug": self.slug})

    def get_absolute_url_online(self):
        """NOTE: it's better to use the version contained in `VersionedContent`, if possible !

        :return:  absolute URL to the public version the content, if `self.public_version` is defined
        :rtype: str
        """

        if self.public_version:
            return self.public_version.get_absolute_url_online()

        return ""

    def get_absolute_contact_url(self, title="Collaboration"):
        """Get url to send a new PM for collaboration

        :param title: what is going to be in the title of the PM before the name of the content
        :type title: str
        :return: url to the PM creation form
        :rtype: str
        """
        get = "?" + urlencode({"title": f"{title} - {self.title}"})

        for author in self.authors.all():
            get += "&" + urlencode({"username": author.username})

        return reverse("mp:create") + get

    def get_repo_path(self, relative=False):
        """Get the path to the tutorial repository

        :param relative: if ``True``, the path will be relative, absolute otherwise.
        :return: physical path
        :rtype: str
        """
        if relative:
            return ""
        else:
            # get the full path (with tutorial/article before it)
            return os.path.join(settings.ZDS_APP["content"]["repo_private_path"], self.slug)

    def ensure_author_gallery(self):
        """
        ensure all authors subscribe to gallery
        """
        author_set = UserGallery.objects.filter(user__in=list(self.authors.all()), gallery=self.gallery).values_list(
            "user__pk", flat=True
        )
        for author in self.authors.all():
            if author.pk in author_set:
                continue
            user_gallery = UserGallery()
            user_gallery.gallery = self.gallery
            user_gallery.mode = GALLERY_WRITE  # write mode
            user_gallery.user = author
            user_gallery.save()

    def can_be_in_beta(self) -> bool:
        return self.type in CONTENT_TYPES_BETA

    def in_beta(self) -> bool:
        """Return True if a beta version of the content exists, and False otherwise."""
        return (self.sha_beta is not None) and (self.sha_beta.strip() != "")

    def in_validation(self) -> bool:
        """Return True if a version of the content is in validation, and False otherwise."""
        return (self.sha_validation is not None) and (self.sha_validation.strip() != "")

    def in_drafting(self) -> bool:
        """Return True if a draft version of the content exists, and False otherwise."""
        return (self.sha_draft is not None) and (self.sha_draft.strip() != "")

    def in_public(self) -> bool:
        """Return True if a public version of the content exists, and False otherwise."""
        return (self.sha_public is not None) and (self.sha_public.strip() != "")

    def is_beta(self, sha: str) -> bool:
        """Return True if the given sha corresponds to the beta version, and False otherwise."""
        return self.in_beta() and sha == self.sha_beta

    def is_validation(self, sha: str) -> bool:
        """Return True if the given sha corresponds to the version in validation, and False otherwise."""
        return self.in_validation() and sha == self.sha_validation

    def get_validation(self):
        # TODO: this function could be improved by declaring explicitly the model Validation
        #  as the support of a ManyToMany relationship in PublishableContent.
        validation = (
            Validation.objects.select_related("validator").filter(content=self).order_by("-date_proposition").first()
        )
        if validation is not None:
            validation.content = self
        return validation

    def is_public(self, sha: str) -> bool:
        """Return True if the given sha corresponds to the public version, and False otherwise."""
        return self.in_public() and sha == self.sha_public

    def is_draft_more_recent_than_public(self) -> bool:
        """Return True if there is a draft version more recent than the published version, and False otherwise."""
        return self.in_public() and self.in_drafting() and self.sha_public != self.sha_draft

    def is_picked(self):
        return self.in_public() and self.sha_public == self.sha_picked

    def is_author(self, user: User) -> bool:
        # This is fast because there are few authors and the QuerySet is usually prefetched and cached.
        return user in self.authors.all()

    def is_permanently_unpublished(self):
        """Is this content permanently unpublished by a moderator ?"""

        return PickListOperation.objects.filter(content=self, operation="REMOVE_PUB", is_effective=True).exists()

    def load_version_or_404(self, sha=None, public=None):
        """Using git, load a specific version of the content. if `sha` is `None`, the draft/public version is used (if
        `public` is `True`).

        :param sha: version
        :param public: if set with the right object, return the public version
        :type public: PublishedContent
        :raise Http404: if sha is not None and related version could not be found
        :return: the versioned content
        :rtype: zds.tutorialv2.models.versioned.VersionedContent
        """
        try:
            return self.load_version(sha, public)
        except (BadObject, BadName, OSError) as error:
            raise Http404(
                "Le code sha existe mais la version demandée ne peut pas être trouvée à cause de {}:{}".format(
                    type(error), str(error)
                )
            )

    @property
    def first_publication_date(self):
        """
        traverse PublishedContent instances to find the first ever published and get its date
        :return: the first publication date
        :rtype: datetime
        """
        return (
            Validation.objects.filter(content=self, status="ACCEPT")
            .order_by("date_validation")
            .values_list("date_validation", flat=True)[0]
        )

    def load_manifest(self, sha=None, public=None):
        """Using git, load a specific version of the manifest. if ``sha`` is ``None``,
        the draft/public version is used (if ``public`` is ``True``).

        :param sha: version
        :param public: if set with the right object, return the public version
        :type public: PublishedContent
        :raise BadObject: if sha is not None and related version could not be found
        :raise OSError: if the path to the repository is wrong
        :raise NotAPublicVersion: if the sha does not correspond to a public version
        :return: the manifest
        :rtype: dict
        """

        # load the good manifest.json
        if sha is None:
            if not public:
                sha = self.sha_draft
            else:
                sha = self.sha_public

        if public and isinstance(public, PublishedContent):  # use the public (altered and not versioned) repository
            path = public.get_prod_path()

            if not os.path.isdir(path):
                raise OSError(path)

            if sha != public.sha_public:
                raise NotAPublicVersion

            with open(os.path.join(path, "manifest.json"), encoding="utf-8") as f:
                manifest = json_handler.loads(f.read())

        else:  # draft version, use the repository (slower, but allows manipulation)
            path = self.get_repo_path()

            if not os.path.isdir(path):
                raise OSError(path)

            repo = Repo(path)
            data = get_blob(repo.commit(sha).tree, "manifest.json")
            try:
                manifest = json_handler.loads(data)
                logger.debug("loaded json")
            except ValueError:
                raise BadManifestError(
                    _("Une erreur est survenue lors de la lecture du manifest.json, est-ce du JSON ?")
                )

        return manifest

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

        max_title_length = PublishableContent._meta.get_field("title").max_length
        json = self.load_manifest(sha=sha, public=public)

        if public and isinstance(public, PublishedContent):
            versioned = get_content_from_json(
                json,
                public.sha_public,
                public.content_public_slug,
                public=True,
                max_title_len=max_title_length,
                hint_licence=self.licence,
            )
        else:
            versioned = get_content_from_json(json, sha, self.slug, max_title_len=max_title_length)

        self.insert_data_in_versioned(versioned)
        return versioned

    def insert_data_in_versioned(self, versioned):
        """Insert some additional data from database in a VersionedContent

        :param versioned: the VersionedContent to fill
        """

        attrs = [
            "pk",
            "authors",
            "subcategory",
            "image",
            "creation_date",
            "pubdate",
            "update_date",
            "source",
            "sha_draft",
            "sha_beta",
            "sha_validation",
            "sha_public",
            "tags",
            "sha_picked",
            "converted_to",
            "type",
        ]

        fns = ["in_beta", "in_validation", "in_public", "get_absolute_contact_url", "get_note_count", "antispam"]

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

        :return: number of notes in the content.
        :rtype: int
        """
        try:
            return self.count_note
        except AttributeError:
            self.count_note = ContentReaction.objects.filter(related_content__pk=self.pk, is_visible=True).count()
            return self.count_note

    def get_last_note(self):
        """
        :return: the last answer in the thread, if any.
        :rtype: ContentReaction|None
        """
        return (
            ContentReaction.objects.all()
            .select_related("related_content")
            .select_related("related_content__public_version")
            .filter(related_content__pk=self.pk)
            .order_by("-pubdate")
            .first()
        )

    def first_note(self):
        """
        :return: the first post of a topic, written by topic's author, if any.
        :rtype: ContentReaction
        """
        return (
            ContentReaction.objects.select_related("related_content")
            .select_related("related_content__public_version")
            .filter(related_content=self)
            .order_by("pubdate")
            .first()
        )

    def last_read_note(self):
        """
        :return: the last post the user has read.
        :rtype: ContentReaction
        """
        user = get_current_user()

        if user and user.is_authenticated:
            try:
                read = (
                    ContentRead.objects.select_related("note")
                    .select_related("note__related_content")
                    .select_related("note__related_content__public_version")
                    .filter(content=self, user__pk=user.pk)
                    .latest("note__pubdate")
                )
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

        if user and user.is_authenticated:
            try:
                read = ContentRead.objects.filter(content=self, user__pk=user.pk).latest("note__pubdate")

                if read and read.note:
                    last_note = read.note

                    next_note = (
                        ContentReaction.objects.select_related("related_content")
                        .select_related("related_content__public_version")
                        .filter(related_content__pk=self.pk, pk__gt=last_note.pk)
                        .select_related("author")
                        .first()
                    )

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

        if user and user.is_authenticated:
            last_user_notes = (
                ContentReaction.objects.filter(related_content=self).filter(author=user.pk).order_by("-position")
            )

            if last_user_notes and last_user_notes[0] == self.last_note:
                last_user_note = last_user_notes[0]
                t = datetime.now() - last_user_note.pubdate
                if t.total_seconds() < settings.ZDS_APP["forum"]["spam_limit_seconds"]:
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
        for tag in filter(None, tag_collection):
            try:
                current_tag, created = Tag.objects.get_or_create(title=tag.lower().strip())
                self.tags.add(current_tag)
            except ValueError as e:
                logger.warning(e)
        logger.debug("Initial number of tags=%s, after filtering=%s", len(tag_collection), len(self.tags.all()))
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


@receiver(post_save, sender=Tag)
def content_tags_changed(instance, created, **kwargs):
    if not created:
        # It is an update of an existing object
        PublishedContent.objects.filter(content__tags=instance.pk).update(search_engine_requires_index=True)


@receiver(post_save, sender=SubCategory)
def content_subcategories_changed(instance, created, **kwargs):
    if not created:
        # It is an update of an existing object
        PublishedContent.objects.filter(content__subcategory=instance.pk).update(search_engine_requires_index=True)


@receiver(post_save, sender=Category)
def content_categories_changed(instance, created, **kwargs):
    if not created:
        # It is an update of an existing object
        PublishedContent.objects.filter(content__subcategory__categorysubcategory__category=instance.pk).update(
            search_engine_requires_index=True
        )


class PublishedContent(AbstractSearchIndexableModel, TemplatableContentModelMixin, OnlineLinkableContentMixin):
    """A class that contains information on the published version of a content.

    Used for quick url resolution, quick listing, and to know where the public version of the files are.

    Linked to a ``PublishableContent`` for the rest. Don't forget to add a ``.prefetch_related('content')`` !!
    """

    objects_per_batch = 25

    class Meta:
        verbose_name = "Contenu publié"
        verbose_name_plural = "Contenus publiés"

    content = models.ForeignKey(PublishableContent, verbose_name="Contenu", on_delete=models.CASCADE)

    content_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True, verbose_name="Type de contenu")
    content_public_slug = models.CharField("Slug du contenu publié", max_length=80)
    content_pk = models.IntegerField("Pk du contenu publié", db_index=True)

    publication_date = models.DateTimeField("Date de publication", db_index=True, blank=True, null=True)
    update_date = models.DateTimeField("Date de mise à jour", db_index=True, blank=True, null=True, default=None)
    sha_public = models.CharField("Sha1 de la version publiée", blank=True, null=True, max_length=80, db_index=True)
    char_count = models.IntegerField(default=None, null=True, verbose_name="Nombre de lettres du contenu", blank=True)

    must_redirect = models.BooleanField(
        "Redirection vers une version plus récente", blank=True, db_index=True, default=False
    )

    authors = models.ManyToManyField(User, verbose_name="Auteurs", db_index=True)

    objects = PublishedContentManager()
    versioned_model = None

    # sizes contain a python dict (as a string in database) with all information about file sizes
    sizes = models.CharField("Tailles des fichiers téléchargeables", max_length=512, default="{}")
    _meta_description = None
    _manifest = None

    @staticmethod
    def get_slug_from_file_path(file_path):
        return os.path.splitext(os.path.split(file_path)[1])[0]

    def __str__(self):
        return _('Version publique de "{}"').format(self.content.title)

    def title(self):
        if self.versioned_model:
            return self.versioned_model.title
        else:
            title = "Default title"
            try:
                self._manifest = self._manifest or self.content.load_manifest(sha=self.sha_public, public=self)
                title = self._manifest.get("title", title)
            except OSError:
                title = self.content.title
            return title

    def description(self):
        if self.versioned_model:
            return self.versioned_model.description
        else:
            self._manifest = self._manifest or self.content.load_manifest(sha=self.sha_public, public=self)
            return self._manifest.get("description", "Default description")

    def meta_description(self):
        """Generate a description for the HTML tag <meta name='description'>"""
        if self._meta_description:
            return self._meta_description
        if not self.versioned_model:
            self.load_public_version()
        self._meta_description = self.versioned_model.description or self.versioned_model.get_introduction() or ""
        if self._meta_description:
            self._meta_description = self._meta_description[: settings.ZDS_APP["forum"]["description_size"]]
        return self._meta_description

    def get_prod_path(self, relative=False):
        if not relative:
            return str(Path(settings.ZDS_APP["content"]["repo_public_path"], self.content_public_slug).absolute())
        else:
            return ""

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
        return os.path.join(self.get_prod_path(), settings.ZDS_APP["content"]["extra_contents_dirname"])

    def has_type(self, type_):
        """check if a given extra content exists

        :return: ``True`` if the file exists, ``False`` otherwhise
        :rtype: bool
        """

        if type_ in ALLOWED_TYPES:
            return Path(self.get_extra_contents_directory(), self.content_public_slug + "." + type_).is_file()

        return False

    def is_exported(self):
        """
        If the content has at least one export, it returns ``True``
        """
        return any(self.has_type(t) for t in ALLOWED_TYPES)

    def has_md(self):
        """Check if the flat markdown version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type("md")

    def has_pdf(self):
        """Check if the pdf version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type("pdf")

    def has_epub(self):
        """Check if the standard epub version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type("epub")

    def has_zip(self):
        """Check if the standard zip version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type("zip")

    def has_tex(self):
        """Check if the latex version of the content is available

        :return: ``True`` if available, ``False`` otherwise
        :rtype: bool
        """
        return self.has_type("tex")

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
                sizes[type_] = os.path.getsize(
                    os.path.join(self.get_extra_contents_directory(), self.content_public_slug + "." + type_)
                )
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
        return self.get_size_file_type("md")

    def get_size_html(self):
        """Get the size of html

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type("html")

    def get_size_pdf(self):
        """Get the size of pdf

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type("pdf")

    def get_size_tex(self):
        """Get the size of LaTeX file

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type("tex")

    def get_size_epub(self):
        """Get the size of epub

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type("epub")

    def get_size_zip(self):
        """Get the size of zip

        :return: size of file
        :rtype: int
        """
        return self.get_size_file_type("zip")

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
                reversed_ + ":download-" + type_, kwargs={"pk": self.content_pk, "slug": self.content_public_slug}
            )
        return ""

    def get_absolute_url_md(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('md')``

        :return: URL to the full markdown version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content("md")

    def get_absolute_url_html(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('html')``

        :return: URL to the HTML version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content("html")

    def get_absolute_url_pdf(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('pdf')``

        :return: URL to the PDF version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content("pdf")

    def get_absolute_url_tex(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('tex')``

        :return: URL to the tex version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content("tex")

    def get_absolute_url_epub(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('epub')``

        :return: URL to the epub version of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content("epub")

    def get_absolute_url_zip(self):
        """wrapper around ``self.get_absolute_url_to_extra_content('zip')``

        :return: URL to the zip archive of the published content
        :rtype: str
        """

        return self.get_absolute_url_to_extra_content("zip")

    def get_absolute_url(self):
        """For admin interface.
        get_absolute_url_online() should probably be directly used in other cases.
        """

        return self.get_absolute_url_online()

    def get_char_count(self, md_file_path=None):
        """Compute the number of letters for a given content

        :param md_file_path: use another file to compute the number of letter rather than the default one.
        :type md_file_path: str
        :return: Number of letters in the md file
        :rtype: int
        """
        if not md_file_path:
            md_file_path = os.path.join(self.get_extra_contents_directory(), self.content_public_slug + ".md")

        try:
            with open(md_file_path, encoding="utf-8") as md_file_handler:
                content = md_file_handler.read()
            current_content = PublishedContent.objects.filter(content_pk=self.content_pk, must_redirect=False).first()
            if current_content:
                return render_markdown_stats(content)
        except OSError as e:
            logger.warning("could not get file %s to compute nb letters (error=%s)", md_file_path, e)

    @property
    def last_publication_date(self):
        return max(self.publication_date, self.update_date or datetime.min)

    @classmethod
    def get_search_document_schema(cls):
        search_engine_schema = super().get_search_document_schema()

        search_engine_schema["fields"] = [
            {"name": "title", "type": "string", "facet": False},  # we search on it
            {"name": "content_pk", "type": "int32", "facet": False},  # we filter on it
            {"name": "content_type", "type": "string", "index": False},
            {"name": "publication_date", "type": "int64", "index": False},
            {"name": "tags", "type": "string[]", "facet": True, "optional": True},  # we search on it
            {"name": "tag_slugs", "type": "string[]", "index": False, "optional": True},
            {"name": "subcategories", "type": "string[]", "facet": True, "optional": True},  # we search on it
            {"name": "categories", "type": "string[]", "facet": True, "optional": True},  # we search on it
            {"name": "text", "type": "string", "facet": False, "optional": True},  # we search on it
            {"name": "description", "type": "string", "facet": False, "optional": True},  # we search on it
            {"name": "get_absolute_url_online", "type": "string", "index": False},
            {"name": "thumbnail", "type": "string", "index": False, "optional": True},
            {"name": "weight", "type": "float"},  # we sort on it
        ]

        return search_engine_schema

    @classmethod
    def get_indexable_objects(cls, force_reindexing=False):
        """Overridden to remove must_redirect=True (and prefetch stuffs)."""

        q = super().get_indexable_objects(force_reindexing)
        return (
            q.prefetch_related("content")
            .prefetch_related("content__tags")
            .prefetch_related("content__subcategory")
            .select_related("content__image")
            .filter(must_redirect=False)
        )

    @classmethod
    def get_indexable(cls, force_reindexing=False):
        """Overridden to also include chapters"""

        search_engine_manager = SearchIndexManager()

        # fetch initial batch
        last_pk = 0
        objects_source = super().get_indexable(force_reindexing)
        objects = list(objects_source.filter(pk__gt=last_pk)[: PublishedContent.objects_per_batch])

        while objects:
            chapters = []

            for content in objects:
                versioned = content.load_public_version()

                # chapters are only indexed for middle and big tuto
                if versioned.has_sub_containers():
                    # delete previous chapters already indexed
                    if not content.search_engine_requires_index:
                        FakeChapter.remove_from_search_engine(search_engine_manager, content.search_engine_id)
                    # (re)index the new one(s)
                    for chapter in versioned.get_list_of_chapters():
                        chapters.append(FakeChapter(chapter, versioned, content.search_engine_id))

            if chapters:
                # since we want to return at most PublishedContent.objects_per_batch items
                # we have to split further
                while chapters:
                    yield chapters[: PublishedContent.objects_per_batch]
                    chapters = chapters[PublishedContent.objects_per_batch :]
            if objects:
                yield objects

            # fetch next batch
            last_pk = objects[-1].pk
            objects = list(objects_source.filter(pk__gt=last_pk)[: PublishedContent.objects_per_batch])

    def get_document_source(self, excluded_fields=[]):
        """Overridden to handle the fact that most information are versioned"""

        excluded_fields.extend(["title", "description", "tags", "categories", "text", "thumbnail", "publication_date"])

        data = super().get_document_source(excluded_fields=excluded_fields)

        # fetch versioned information
        versioned = self.load_public_version()

        data["title"] = versioned.title
        data["description"] = versioned.description
        data["publication_date"] = date_to_timestamp_int(self.publication_date)

        data["tags"] = []
        data["tag_slugs"] = []
        for tag in versioned.tags.all():
            data["tags"].append(tag.title)
            data["tag_slugs"].append(tag.slug)  # store also slugs to have them from search results

        if self.content.image:
            data["thumbnail"] = self.content.image.physical["content_thumb"].url

        data["categories"] = []
        data["subcategories"] = []
        for subcategory in versioned.subcategory.all():
            parent_category = subcategory.get_parent_category()
            if subcategory.slug not in data["subcategories"]:
                data["subcategories"].append(subcategory.slug)
            if parent_category and parent_category.slug not in data["categories"]:
                data["categories"].append(parent_category.slug)

        if versioned.has_extracts():
            data["text"] = clean_html(versioned.get_content_online())

        is_multipage = versioned.has_sub_containers()
        data["weight"] = self._get_search_weight(is_multipage)

        return data

    def _get_search_weight(self, is_multipage: bool):
        """
        Calculate the weight used to sort search results.
        We make a difference between validated content (either single or multipage) and content published freely
        (picked for the front page or not).
        """
        weights = settings.ZDS_APP["search"]["boosts"]["publishedcontent"]

        if self.content.requires_validation():
            if is_multipage:
                return weights["if_validated_and_multipage"]
            else:
                return weights["if_validated"]
        else:
            assert self.content_type == "OPINION"
            if self.content.is_picked():
                return weights["if_opinion"]
            else:
                return weights["if_opinion_not_picked"]

    @classmethod
    def get_search_query(cls):
        return {
            "query_by": "title,description,categories,subcategories,tags,text",
            "query_by_weights": "{},{},{},{},{},{}".format(
                settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["title"],
                settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["description"],
                settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["categories"],
                settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["subcategories"],
                settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["tags"],
                settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["text"],
            ),
            "sort_by": "weight:desc",
        }


@receiver(pre_delete, sender=PublishedContent)
def delete_published_content_in_search_engine(sender, instance, **kwargs):
    """Catch the pre_delete signal to ensure the deletion in the search engine.
    Also, handle the deletion of the corresponding chapters.
    """

    search_engine_manager = SearchIndexManager()

    FakeChapter.remove_from_search_engine(search_engine_manager, instance.search_engine_id)
    search_engine_manager.delete_document(instance)


@receiver(pre_save, sender=PublishedContent)
def delete_published_content_in_search_engine_if_set_to_redirect(sender, instance, **kwargs):
    """If the slug of the content changes, the ``must_redirect`` field is set
    to ``True`` and a new PublishedContnent is created. To avoid duplicates,
    the previous ones must be removed from the search engine.
    """

    try:
        obj = PublishedContent.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass  # nothing to worry about
    else:
        if not obj.must_redirect and instance.must_redirect:
            delete_published_content_in_search_engine(sender, instance, **kwargs)


class FakeChapter(AbstractSearchIndexable):
    """A simple class that is used by Typesense to index chapters, constructed from the containers.

    In schema, this class defines PublishedContent as its parent. Also, indexing is done by the parent.

    Note that this class is only indexable, not updatable, since it cannot maintain a value of ``search_engine_requires_index``.
    """

    parent_model = PublishedContent
    text = ""
    title = ""
    parent_id = ""
    get_absolute_url_online = ""
    parent_title = ""
    parent_get_absolute_url_online = ""
    parent_publication_date = ""
    thumbnail = ""
    categories = None
    subcategories = None

    def __init__(self, chapter, main_container, parent_id):
        self.title = chapter.title
        self.text = chapter.get_content_online()
        self.parent_id = parent_id
        self.get_absolute_url_online = chapter.get_absolute_url_online()

        self.search_engine_id = (
            main_container.slug + "__" + chapter.slug
        )  # both slugs are unique by design, so id remains unique

        self.parent_title = main_container.title
        self.parent_get_absolute_url_online = main_container.get_absolute_url_online()
        self.parent_publication_date = main_container.pubdate

        if main_container.image:
            self.thumbnail = main_container.image.physical["content_thumb"].url

        self.categories = []
        self.subcategories = []
        for subcategory in main_container.subcategory.all():
            parent_category = subcategory.get_parent_category()
            if subcategory.slug not in self.subcategories:
                self.subcategories.append(subcategory.slug)
            if parent_category and parent_category.slug not in self.categories:
                self.categories.append(parent_category.slug)

    @classmethod
    def get_search_document_type(cls):
        return "chapter"

    @classmethod
    def get_search_document_schema(self):
        search_engine_schema = super().get_search_document_schema()

        search_engine_schema["fields"] = [
            {"name": "parent_id", "type": "string", "facet": False},  # we filter on it when content is removed
            {"name": "title", "type": "string", "facet": False},  # we search on it
            {"name": "parent_title", "type": "string", "index": False},
            {"name": "parent_publication_date", "type": "int64", "index": False},
            {"name": "text", "type": "string", "facet": False},  # we search on it
            {"name": "get_absolute_url_online", "type": "string", "index": False},
            {"name": "parent_get_absolute_url_online", "type": "string", "index": False},
            {"name": "thumbnail", "type": "string", "index": False},
            {"name": "weight", "type": "float", "facet": False},  # we sort on it
        ]

        return search_engine_schema

    def get_document_source(self, excluded_fields=[]):
        """Overridden to handle the fact that most information are versioned"""

        excluded_fields.extend(["text"])

        data = super().get_document_source(excluded_fields=excluded_fields)
        data["parent_publication_date"] = date_to_timestamp_int(self.parent_publication_date)
        data["weight"] = settings.ZDS_APP["search"]["boosts"]["chapter"]["global"]
        data["text"] = clean_html(self.text)

        return data

    @classmethod
    def get_search_query(cls):
        return {
            "query_by": "title,text",
            "query_by_weights": "{},{}".format(
                settings.ZDS_APP["search"]["boosts"]["chapter"]["title"],
                settings.ZDS_APP["search"]["boosts"]["chapter"]["text"],
            ),
            "sort_by": "weight:desc",
        }

    @classmethod
    def remove_from_search_engine(cls, search_engine_manager: SearchIndexManager, parent_search_engine_id: int):
        filter_by = SearchFilter()
        filter_by.add_exact_filter("parent_id", parent_search_engine_id)

        search_engine_manager.delete_by_query(cls.get_search_document_type(), {"filter_by": str(filter_by)})


class ContentReaction(Comment):
    """
    A comment written by any user about a PublishableContent they just read.
    """

    class Meta:
        verbose_name = "note sur un contenu"
        verbose_name_plural = "notes sur un contenu"

    related_content = models.ForeignKey(
        PublishableContent,
        verbose_name="Contenu",
        on_delete=models.CASCADE,
        related_name="related_content_note",
        db_index=True,
    )

    objects = ReactionManager()

    def __str__(self):
        return f"<Réaction pour '{self.related_content}', #{self.pk}>"

    def get_absolute_url(self):
        """Find the url to the reaction

        :return: the url of the comment
        :rtype: str
        """
        page = int(ceil(float(self.position) / settings.ZDS_APP["content"]["notes_per_page"]))
        return f"{self.related_content.get_absolute_url_online()}?page={page}#p{self.pk}"

    def get_notification_title(self):
        return self.related_content.title


class ContentRead(models.Model):
    """
    Small model which keeps track of the user viewing tutorials.

    It remembers the PublishableContent they read and what was the last Note at that time.
    """

    class Meta:
        verbose_name = "Contenu lu"
        verbose_name_plural = "Contenus lus"

    content = models.ForeignKey(PublishableContent, db_index=True, on_delete=models.CASCADE)
    note = models.ForeignKey(ContentReaction, db_index=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, related_name="content_notes_read", db_index=True, on_delete=models.CASCADE)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Save this model but check that if we have not a related note it is because the user is content author.
        """
        if self.user not in self.content.authors.all() and self.note is None:
            raise ValueError(_("La note doit exister ou l'utilisateur doit être l'un des auteurs."))

        return super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f'<Contenu "{self.content}" lu par {self.user}, #{self.note.pk}>'


class Validation(models.Model):
    """
    Content validation.
    """

    class Meta:
        verbose_name = "Validation"
        verbose_name_plural = "Validations"

    content = models.ForeignKey(
        PublishableContent,
        null=True,
        blank=True,
        verbose_name="Contenu proposé",
        db_index=True,
        on_delete=models.CASCADE,
    )
    version = models.CharField("Sha1 de la version", blank=True, null=True, max_length=80, db_index=True)
    date_proposition = models.DateTimeField("Date de proposition", db_index=True, null=True, blank=True)
    comment_authors = models.TextField("Commentaire de l'auteur", null=True, blank=True)
    validator = models.ForeignKey(
        User,
        verbose_name="Validateur",
        related_name="author_content_validations",
        blank=True,
        null=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )
    date_reserve = models.DateTimeField("Date de réservation", blank=True, null=True)
    date_validation = models.DateTimeField("Date de validation", blank=True, null=True)
    comment_validator = models.TextField("Commentaire du validateur", blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    def __str__(self):
        return _("Validation de « {} »").format(self.content.title)

    def is_pending(self):
        """Check if the validation is pending

        :return: ``True`` if status is pending, ``False`` otherwise
        :rtype: bool
        """
        return self.status == "PENDING"

    def is_pending_valid(self):
        """Check if the validation is pending (but there is a validator)

        :return: ``True`` if status is pending/valid, ``False`` otherwise
        :rtype: bool
        """
        return self.status == "PENDING_V"

    def is_accept(self):
        """Check if the content is accepted

        :return: ``True`` if status is accepted, ``False`` otherwise
        :rtype: bool
        """
        return self.status == "ACCEPT"

    def is_reject(self):
        """Check if the content is rejected

        :return: ``True`` if status is rejected, ``False`` otherwise
        :rtype: bool
        """
        return self.status == "REJECT"

    def is_cancel(self):
        """Check if the content is canceled

        :return: ``True`` if status is canceled, ``False`` otherwise
        :rtype: bool
        """
        return self.status == "CANCEL"


class PickListOperation(models.Model):
    class Meta:
        verbose_name = "Choix d'un billet"
        verbose_name_plural = "Choix des billets"

    content = models.ForeignKey(
        PublishableContent,
        null=False,
        blank=False,
        verbose_name="Contenu proposé",
        db_index=True,
        on_delete=models.CASCADE,
    )
    operation = models.CharField(
        null=False, blank=False, db_index=True, max_length=len("REMOVE_PUB"), choices=PICK_OPERATIONS
    )
    operation_date = models.DateTimeField(null=False, db_index=True, verbose_name="Date de l'opération")
    version = models.CharField(null=False, blank=False, max_length=128, verbose_name="Version du billet concernée")
    staff_user = models.ForeignKey(
        User, null=False, blank=False, on_delete=CASCADE, verbose_name="Modérateur", related_name="pick_operations"
    )
    canceler_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=CASCADE,
        verbose_name="Modérateur qui a annulé la décision",
        related_name="canceled_pick_operations",
    )
    is_effective = models.BooleanField(verbose_name="Choix actif", default=True)

    def __str__(self):
        return f"{self.get_operation_display()} : {self.content}"

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
        if self.content is not None and self.content.type == "OPINION":
            return super().save(**kwargs)
        raise ValueError("Content cannot be null or something else than opinion.", self.content)


STATE_CHOICES = [
    ("REQUESTED", _("Export demandé")),
    ("RUNNING", _("Export en cours")),
    ("SUCCESS", _("Export réalisé")),
    ("FAILURE", _("Export échoué")),
]


class PublicationEvent(models.Model):
    class Meta:
        verbose_name = _("Événement de publication")
        verbose_name_plural = _("Événements de publication")

    published_object = models.ForeignKey(
        PublishedContent, null=False, on_delete=models.CASCADE, verbose_name="contenu publié"
    )
    state_of_processing = models.CharField(choices=STATE_CHOICES, null=False, blank=False, max_length=20, db_index=True)
    # 25 for formats such as "printable.pdf", if tomorrow we want other "long" formats this will be ready
    format_requested = models.CharField(blank=False, null=False, max_length=25)
    created = models.DateTimeField(verbose_name="date de création", name="date", auto_now_add=True)

    def __str__(self):
        return f"{self.published_object.title()}: {self.format_requested} - {self.state_of_processing}"

    def url(self):
        return self.published_object.get_absolute_url_to_extra_content(self.format_requested)


class ContentContributionRole(models.Model):
    """
    Contribution role of content
    """

    class Meta:
        verbose_name = "Role de la contribution au contenu"
        verbose_name_plural = "Roles de la contribution au contenu"

    title = models.CharField(null=False, blank=False, max_length=80)
    subtitle = models.CharField(null=True, blank=True, max_length=200)
    position = models.IntegerField(default=0)

    def __str__(self):
        return f"<Role de type '{self.title}', #{self.pk}>"


class ContentContribution(models.Model):
    """
    Content contributions
    """

    class Meta:
        verbose_name = "Contribution aux contenus"
        verbose_name_plural = "Contributions aux contenus"

    contribution_role = models.ForeignKey(
        ContentContributionRole,
        null=False,
        verbose_name="role de la contribution",
        db_index=True,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(User, null=False, verbose_name="Contributeur", db_index=True, on_delete=models.CASCADE)
    content = models.ForeignKey(
        PublishableContent, null=False, verbose_name="Contenu", db_index=True, on_delete=models.CASCADE
    )
    comment = models.CharField(verbose_name="Commentaire", null=True, blank=True, max_length=200)

    def __str__(self):
        return "<Contribution a '{}' par {} de type {}, #{}>".format(
            self.content.title, self.user.username, self.contribution_role.title, self.pk
        )


class ContentSuggestion(models.Model):
    class Meta:
        verbose_name = "Suggestion de publication"
        verbose_name_plural = "Suggestions de publication"

    publication = models.ForeignKey(
        PublishableContent,
        null=False,
        verbose_name="Publication",
        db_index=True,
        on_delete=models.CASCADE,
        related_name="publication",
    )
    suggestion = models.ForeignKey(
        PublishableContent,
        null=False,
        verbose_name="Suggestion",
        db_index=True,
        on_delete=models.CASCADE,
        related_name="suggestion",
    )

    def __str__(self):
        return f"<Suggest '{self.suggestion.title}' for content '{self.publication.title}', #{self.pk}>"

    @staticmethod
    def get_random_public_suggestions(publication: PublishableContent, count: int):
        """
        Get random public suggestions for the given publication.
        At most `count` suggestions are returned.
        """
        all_suggestions = (
            ContentSuggestion.objects.filter(publication=publication).order_by("?").prefetch_related("suggestion")
        )
        public_suggestions = [suggestion for suggestion in all_suggestions if suggestion.suggestion.in_public()]
        return public_suggestions[:count]


@receiver(models.signals.pre_delete, sender=User)
def transfer_paternity_receiver(sender, instance, **kwargs):
    """
    transfer paternity to external user on user deletion
    """
    external = get_external_account()
    PublishableContent.objects.transfer_paternity(instance, external, UserGallery)
    PublishedContent.objects.transfer_paternity(instance, external)


import zds.tutorialv2.receivers  # noqa
