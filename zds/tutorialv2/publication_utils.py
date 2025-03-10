import contextlib
import copy
import logging
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from os import makedirs, path
from pathlib import Path

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from zds.forum.utils import lock_topic, send_post
from zds.tutorialv2 import signals
from zds.tutorialv2.epub_utils import build_ebook
from zds.tutorialv2.models.database import ContentReaction, PublicationEvent, PublishedContent
from zds.tutorialv2.publish_container import publish_use_manifest
from zds.tutorialv2.signals import content_unpublished
from zds.tutorialv2.utils import export_content
from zds.utils.templatetags.emarkdown import render_markdown
from zds.utils.templatetags.smileys_def import LICENSES_BASE_PATH, SMILEYS_BASE_PATH

logger = logging.getLogger(__name__)
licences = {
    "by-nc-nd": "by-nc-nd.svg",
    "by-nc-sa": "by-nc-sa.svg",
    "by-nc": "by-nc.svg",
    "by-nd": "by-nd.svg",
    "by-sa": "by-sa.svg",
    "by": "by.svg",
    "0": "0.svg",
    "copyright": "copyright.svg",
}


def notify_update(db_object, is_update, is_major):
    if not is_update or is_major:
        # Follow
        signals.content_published.send(sender=db_object.__class__, instance=db_object, by_email=False)


def publish_content(db_object, versioned, is_major_update=True):
    """
    Publish a given content.

    .. note::
        create a manifest.json without the introduction and conclusion if not needed. Also remove the 'text' field
        of extracts.

    :param db_object: Database representation of the content
    :type db_object: zds.tutorialv2.models.database.PublishableContent
    :param versioned: version of the content to publish
    :type versioned: zds.tutorialv2.models.versioned.VersionedContent
    :param is_major_update: if set to `True`, will update the publication date
    :type is_major_update: bool
    :raise FailureDuringPublication: if something goes wrong
    :return: the published representation
    :rtype: zds.tutorialv2.models.database.PublishedContent
    """

    from zds.tutorialv2.models.database import PublishedContent

    if is_major_update:
        versioned.pubdate = datetime.now()

    # First write the files to a temporary directory: if anything goes wrong,
    # the last published version is not impacted !
    tmp_path = path.join(settings.ZDS_APP["content"]["repo_public_path"], versioned.slug + "__building")
    if path.exists(tmp_path):
        shutil.rmtree(tmp_path)  # remove previous attempt, if any

    # render HTML:
    altered_version = copy.deepcopy(versioned)
    char_count = publish_use_manifest(db_object, tmp_path, altered_version)
    altered_version.dump_json(path.join(tmp_path, "manifest.json"))

    # make room for 'extra contents'
    build_extra_contents_path = path.join(tmp_path, settings.ZDS_APP["content"]["extra_contents_dirname"])
    makedirs(build_extra_contents_path)
    base_name = path.join(build_extra_contents_path, versioned.slug)

    # 1. markdown file (base for the others) :
    # If we come from a command line, we need to activate i18n, to have the date in the french language.
    cur_language = translation.get_language()
    altered_version.pubdate = datetime.now()

    md_file_path = base_name + ".md"
    with contextlib.suppress(OSError):
        Path(Path(md_file_path).parent, "images").mkdir()
    is_update = False

    if db_object.public_version:
        public_version = update_existing_publication(db_object, versioned)
        is_update = True
    else:
        public_version = PublishedContent()

    # make the new public version
    public_version.content_public_slug = versioned.slug
    public_version.content_type = versioned.type
    public_version.content_pk = db_object.pk
    public_version.content = db_object
    public_version.char_count = char_count
    public_version.save()
    with contextlib.suppress(FileExistsError):
        makedirs(public_version.get_extra_contents_directory())
    if is_major_update or not is_update:
        public_version.publication_date = datetime.now()
    elif is_update:
        public_version.update_date = datetime.now()
    public_version.sha_public = versioned.current_version
    public_version.save(update_fields=["publication_date", "update_date", "sha_public"])

    public_version.authors.clear()
    for author in db_object.authors.all():
        public_version.authors.add(author)

    # this puts the manifest.json and base json file on the prod path.
    shutil.rmtree(public_version.get_prod_path(), ignore_errors=True)
    shutil.copytree(tmp_path, public_version.get_prod_path())
    db_object.sha_public = versioned.current_version
    public_version.save()
    if settings.ZDS_APP["content"]["extra_content_generation_policy"] == "SYNC":
        # ok, now we can really publish the thing!
        generate_external_content(base_name, build_extra_contents_path, md_file_path, versioned=versioned)
    elif settings.ZDS_APP["content"]["extra_content_generation_policy"] == "WATCHDOG":
        PublicatorRegistry.get("watchdog").publish(md_file_path, base_name, silently_pass=False)

    return public_version


def update_existing_publication(db_object, versioned):
    public_version = db_object.public_version
    # the content has been published in the past, so we will clean up old files!
    old_path = public_version.get_prod_path()

    # if the slug has changed, create a new object instead of reusing the old one
    # this allows us to handle permanent redirection so that SEO is not impacted.
    if versioned.slug != public_version.content_public_slug:
        public_version.must_redirect = True  # set redirection
        public_version.save(update_fields=["must_redirect"])
        publication_date = public_version.publication_date
        db_object.public_version = PublishedContent()
        public_version = db_object.public_version

        # keep the same publication date if the content is already published
        public_version.publication_date = publication_date

    # remove old files only if everything succeed so far: if something bad
    # happened, we don't want to have a published content without content!
    logging.getLogger(__name__).debug("erase " + old_path)
    shutil.rmtree(old_path)

    return public_version


def write_md_file(md_file_path, parsed_with_local_images, versioned):
    with open(md_file_path, "w", encoding="utf-8") as md_file:
        try:
            md_file.write(parsed_with_local_images)
        except UnicodeError:
            logger.error("Could not encode %s in UTF-8, publication aborted", versioned.title)
            raise FailureDuringPublication(
                _(
                    "Une erreur est survenue durant la génération du fichier markdown "
                    "à télécharger, vérifiez le code markdown"
                )
            )


def generate_external_content(base_name, extra_contents_path, md_file_path, excluded=None, **kwargs):
    """
    generate all static file that allow offline access to content

    :param base_name: base nae of file (without extension)
    :param extra_contents_path: internal directory where all files will be pushed
    :param md_file_path: bundled markdown file path
    :param excluded: list of excluded format, None if no exclusion
    """
    excluded = excluded or ["watchdog"]
    for publicator_name, publicator in PublicatorRegistry.get_all_registered(excluded):
        try:
            publicator.publish(
                md_file_path,
                base_name,
                change_dir=extra_contents_path,
                cur_language=translation.get_language(),
                **kwargs,
            )
        except (FailureDuringPublication, OSError):
            logging.getLogger(__name__).exception(
                "Could not publish %s format from %s base.", publicator_name, md_file_path
            )


class PublicatorRegistry:
    """
    Register all publicator as a 'human-readable name/publicator' instance key/value list
    """

    registry = {}

    @classmethod
    def register(cls, publicator_name, *args):
        def decorated(func):
            cls.registry[publicator_name] = func(*args)
            return func

        return decorated

    @classmethod
    def get_all_registered(cls, exclude=None):
        """
        Args:
            exclude: A list of excluded publicator

        Returns:
        """
        if exclude is None:
            exclude = []
        order_key = {
            "zip": 1,
            "md": 2,
            "html": 3,
            "epub": 4,
            "pdf": 5,
        }
        for key, value in sorted(cls.registry.items(), key=lambda k: order_key.get(k[0], 42)):
            if key not in exclude:
                yield key, value

    @classmethod
    def unregister(cls, name):
        """
        Remove registered Publicator named 'name' if present

        :param name: publicator name.
        """
        if name in cls.registry:
            del cls.registry[name]

    @classmethod
    def get(cls, name):
        """
        Get publicator named 'name'.

        :param name:
        :return: the wanted publicator
        :rtype: Publicator
        :raise KeyError: if publicator is not registered
        """
        return cls.registry[name]


class Publicator:
    """
    Publicator base object, all methods must be overridden
    """

    def publish(self, md_file_path, base_name, **kwargs):
        """
        Function called to generate a content export

        :param md_file_path: base markdown file path
        :param base_name: file name without extension
        :param kwargs: other publicator dependent options
        """
        raise NotImplementedError()

    def get_published_content_entity(self, md_file_path) -> PublishedContent:
        """
        Retrieve the db entity from mdfile path

        :param md_file_path: mdfile path as string
        :type md_file_path: str
        :return: the db entity
        :rtype: zds.tutorialv2.models.models_database.PublishedContent
        """
        content_slug = PublishedContent.get_slug_from_file_path(md_file_path)
        published_content_entity = PublishedContent.objects.filter(content_public_slug=content_slug).first()
        return published_content_entity


@PublicatorRegistry.register("md")
class MarkdownPublicator(Publicator):
    def publish(self, md_file_path, base_name, *, cur_language=settings.LANGUAGE_CODE, **kwargs):
        published_content_entity = self.get_published_content_entity(md_file_path)
        versioned = kwargs.pop("versioned", None)
        if not versioned:
            # do not use load_public_version as it lacks of information to get the content
            # if you use it you will only get titles, without the text
            versioned = published_content_entity.content.load_version(sha=published_content_entity.sha_public)
        try:
            translation.activate(settings.LANGUAGE_CODE)
            parsed = render_to_string("tutorialv2/export/content.md", {"content": versioned})
        except requests.exceptions.HTTPError:
            raise FailureDuringPublication("Could not publish flat markdown")
        finally:
            translation.activate(cur_language)

        write_md_file(md_file_path, parsed, versioned)
        if "__building" in md_file_path:
            shutil.copy2(md_file_path, md_file_path.replace("__building", ""))


def _read_flat_markdown(md_file_path):
    with open(md_file_path, encoding="utf-8") as md_file_handler:
        md_flat_content = md_file_handler.read()
    return md_flat_content


@PublicatorRegistry.register("zip")
class ZipPublicator(Publicator):
    def publish(self, md_file_path, base_name, **kwargs):
        try:
            published_content_entity = self.get_published_content_entity(md_file_path)
            if published_content_entity is None:
                raise ValueError("published_content_entity is None")
            if published_content_entity.content.type == "OPINION" and not settings.ZDS_APP["opinions"]["allow_zip"]:
                logger.info("ZIP not allowed for opinions.")
                return
            make_zip_file(published_content_entity)
            # no need to move zip file because it is already dumped to the public directory
        except (OSError, ValueError) as e:
            raise FailureDuringPublication("Zip could not be created", e)


@PublicatorRegistry.register("pdf")
class ZMarkdownRebberLatexPublicator(Publicator):
    """
    Use zmarkdown and rebber stringifier to produce latex & pdf output.
    """

    def __init__(self, extension=".pdf", latex_classes=""):
        self.extension = extension
        self.doc_type = extension[1:]
        self.latex_classes = latex_classes

    def publish(self, md_file_path, base_name, **kwargs):
        published_content_entity = self.get_published_content_entity(md_file_path)
        if published_content_entity.content.type == "OPINION" and not settings.ZDS_APP["opinions"]["allow_pdf"]:
            logger.info("PDF not allowed for opinions")
            return
        gallery_pk = published_content_entity.content.gallery.pk
        depth_to_size_map = {
            1: "small",  # in fact this is an "empty" tutorial (i.e it is empty or has intro and/or conclusion)
            2: "small",
            3: "middle",
            4: "big",
        }
        public_versionned_source = published_content_entity.content.load_version(
            sha=published_content_entity.sha_public
        )
        base_directory = Path(base_name).parent
        image_dir = base_directory / "images"
        with contextlib.suppress(FileExistsError):
            image_dir.mkdir(parents=True)
        if (settings.MEDIA_ROOT / "galleries" / str(gallery_pk)).exists():
            for image in (settings.MEDIA_ROOT / "galleries" / str(gallery_pk)).iterdir():
                with contextlib.suppress(OSError):
                    shutil.copy2(str(image.absolute()), str(image_dir))
        content_type = depth_to_size_map[public_versionned_source.get_tree_level()]
        if self.latex_classes:
            content_type += ", " + self.latex_classes
        title = published_content_entity.title()
        authors = [a.username for a in published_content_entity.authors.all()]

        licence = published_content_entity.content.licence.code
        licence_short = licence.replace("CC", "").strip().lower()
        licence_logo = licences.get(licence_short, False)
        if licence_logo:
            licence_url = f"https://creativecommons.org/licenses/{licence_short}/4.0/legalcode"
            # we need a specific case for CC-0 as it is "public-domain"
            if licence_logo == licences["0"]:
                licence_url = "https://creativecommons.org/publicdomain/zero/1.0/legalcode.fr"
        else:
            licence = str(_("Tous droits réservés"))
            licence_logo = licences["copyright"]
            licence_url = ""

        replacement_image_url = str(settings.MEDIA_ROOT.parent)
        if not replacement_image_url.endswith("/"):
            replacement_image_url += "/"
        replaced_media_url = settings.MEDIA_URL
        if replaced_media_url.startswith("/"):
            replaced_media_url = replaced_media_url[1:]
        exported = export_content(public_versionned_source, with_text=True, ready_to_publish_only=True)
        # no title to avoid zmd to put it on the final latex
        del exported["title"]
        content, metadata, messages = render_markdown(
            exported,
            output_format="texfile",
            # latex template arguments
            content_type=content_type,
            title=title,
            authors=authors,
            license=licence,
            license_directory=str(LICENSES_BASE_PATH),
            license_logo=licence_logo,
            license_url=licence_url,
            smileys_directory=str(SMILEYS_BASE_PATH / "svg"),
            images_download_dir=str(base_directory / "images"),
            local_url_to_local_path=["/", replacement_image_url],
            heading_shift=-1,
            date=date(published_content_entity.last_publication_date, "l d F Y"),
        )
        if content == "" and messages:
            raise FailureDuringPublication(f"Markdown was not parsed due to {messages}")
        zmd_class_dir_path = Path(settings.ZDS_APP["content"]["latex_template_repo"])
        content.replace(replacement_image_url + replaced_media_url, replacement_image_url)
        if zmd_class_dir_path.exists() and zmd_class_dir_path.is_dir():
            with contextlib.suppress(FileExistsError):
                zmd_class_link = base_directory / "zmdocument.cls"
                zmd_class_link.symlink_to(zmd_class_dir_path / "zmdocument.cls")
                luatex_dir_link = base_directory / "utf8.lua"
                luatex_dir_link.symlink_to(zmd_class_dir_path / "utf8.lua", target_is_directory=True)
        true_latex_extension = ".".join(self.extension.split(".")[:-1]) + ".tex"
        latex_file_path = base_name + true_latex_extension
        pdf_file_path = base_name + self.extension
        default_logo_original_path = Path(__file__).parent / ".." / ".." / "assets" / "images" / "logo@2x.png"
        with contextlib.suppress(FileExistsError):
            shutil.copy(str(default_logo_original_path), str(base_directory / "default_logo.png"))
        with open(latex_file_path, mode="w", encoding="utf-8") as latex_file:
            latex_file.write(content)
        shutil.copy2(latex_file_path, published_content_entity.get_extra_contents_directory())

        self.full_tex_compiler_call(latex_file_path, draftmode="-draftmode")
        self.full_tex_compiler_call(latex_file_path, draftmode="-draftmode")
        self.make_glossary(base_name.split("/")[-1], latex_file_path)
        self.full_tex_compiler_call(latex_file_path)

        shutil.copy2(pdf_file_path, published_content_entity.get_extra_contents_directory())

    def full_tex_compiler_call(self, latex_file, draftmode: str = ""):
        success_flag = self.tex_compiler(latex_file, draftmode)
        if not success_flag:
            handle_tex_compiler_error(latex_file, self.extension)

    def handle_makeglossaries_error(self, latex_file):
        with open(path.splitext(latex_file)[0] + ".log") as latex_log:
            errors = "\n".join(filter(line for line in latex_log if "fatal" in line.lower() or "error" in line.lower()))
        raise FailureDuringPublication(errors)

    def tex_compiler(self, texfile, draftmode: str = ""):
        command = f"lualatex -shell-escape -interaction=nonstopmode {draftmode} {texfile}"
        command_process = subprocess.Popen(
            command, shell=True, cwd=path.dirname(texfile), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # let's put 10 min of timeout because we do not generate latex everyday
        command_process.communicate(timeout=600)

        pdf_file_path = path.splitext(texfile)[0] + self.extension
        return path.exists(pdf_file_path)

    def make_glossary(self, basename, texfile):
        command = f"makeglossaries {basename}"
        command_process = subprocess.Popen(
            command, shell=True, cwd=path.dirname(texfile), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        std_out, std_err = command_process.communicate()

        # TODO: check makeglossary exit codes to see if we can enhance error detection
        if "fatal" not in std_out.decode("utf-8").lower() and "fatal" not in std_err.decode("utf-8").lower():
            return True

        self.handle_makeglossaries_error(texfile)


def handle_tex_compiler_error(latex_file_path, ext):
    # TODO zmd: fix extension parsing
    log_file_path = latex_file_path[:-3] + "log"
    errors = [f"Error occured, log file {log_file_path} not found."]
    with contextlib.suppress(FileNotFoundError, UnicodeDecodeError):
        with Path(log_file_path).open(encoding="utf-8") as latex_log:
            print_context = 25
            lines = []
            relevant_line = -print_context
            for idx, line in enumerate(latex_log):
                if "fatal" in line.lower() or "error" in line.lower():
                    relevant_line = idx
                    lines.append(line)
                elif idx - relevant_line < print_context:
                    lines.append(line)

            errors = "\n".join(lines)
    logger.debug("%s ext=%s", errors, ext)

    raise FailureDuringPublication(errors)


@PublicatorRegistry.register("epub")
class ZMarkdownEpubPublicator(Publicator):
    def publish(self, md_file_path, base_name, **kwargs):
        try:
            published_content_entity = self.get_published_content_entity(md_file_path)
            if published_content_entity.content.type == "OPINION" and not settings.ZDS_APP["opinions"]["allow_epub"]:
                logger.info("EPUB not allowed for opinions")
                return
            epub_file_path = Path(base_name + ".epub")
            logger.info("Start generating epub")
            build_ebook(published_content_entity, path.dirname(md_file_path), epub_file_path)
        except (OSError, requests.exceptions.HTTPError):
            raise FailureDuringPublication("Error while generating epub file.")
        else:
            logger.info(epub_file_path)
            epub_path = Path(published_content_entity.get_extra_contents_directory(), Path(epub_file_path.name))
            if epub_path.exists():
                os.remove(str(epub_path))
            if not epub_path.parent.exists():
                epub_path.parent.mkdir(parents=True)
            logger.info(
                "created %s. moving it to %s", epub_file_path, published_content_entity.get_extra_contents_directory()
            )
            shutil.move(str(epub_file_path), published_content_entity.get_extra_contents_directory())


@PublicatorRegistry.register("watchdog")
class WatchdogFilePublicator(Publicator):
    def publish(self, md_file_path, base_name, silently_pass=True, **kwargs):
        if silently_pass:
            return
        published_content = self.get_published_content_entity(md_file_path)
        self.publish_from_published_content(published_content)

    def publish_from_published_content(self, published_content: PublishedContent):
        for requested_format in PublicatorRegistry.get_all_registered(["watchdog"]):
            # Remove previous PublicationEvent for this content, not handled by
            # the publication watchdog yet:
            PublicationEvent.objects.filter(
                state_of_processing="REQUESTED",
                published_object__content_pk=published_content.content_pk,
                format_requested=requested_format[0],
            ).delete()
            PublicationEvent.objects.create(
                state_of_processing="REQUESTED",
                published_object=published_content,
                format_requested=requested_format[0],
            )


class FailureDuringPublication(Exception):
    """Exception raised if something goes wrong during publication process"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def make_zip_file(published_content):
    """Create the zip archive extra content from the published content

    :param published_content: a PublishedContent object
    :return:
    """

    publishable = published_content.content
    # update SHA so that archive gets updated too
    publishable.sha_public = publishable.sha_draft
    file_path = path.join(
        published_content.get_extra_contents_directory(), published_content.content_public_slug + ".zip"
    )
    zip_file = zipfile.ZipFile(file_path, "w")
    versioned = publishable.load_version(None, True)
    from zds.tutorialv2.views.archives import DownloadContent

    DownloadContent.insert_into_zip(zip_file, versioned.repository.commit(versioned.current_version).tree)
    zip_file.close()
    return file_path


def unpublish_content(db_object, moderator=None):
    """
    Remove the given content from the public view.

    .. note::
        This will send content_unpublished event.

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :param moderator: the staff user who triggered the unpublish action.
    :type moderator: django.contrib.auth.models.User
    :return: ``True`` if unpublished, ``False`` otherwise
    :rtype: bool
    """

    from zds.tutorialv2.models.database import PublishedContent

    with contextlib.suppress(ObjectDoesNotExist, OSError):
        public_version = PublishedContent.objects.get(pk=db_object.public_version.pk)

        results = [
            content_unpublished.send(
                sender=reaction.__class__, instance=db_object, target=ContentReaction, moderator=moderator, user=None
            )
            for reaction in [ContentReaction.objects.filter(related_content=db_object).all()]
        ]
        logging.debug("Nb_messages=%d, messages=%s", len(results), results)
        # remove public_version:
        public_version.delete()
        update_params = {"public_version": None}

        if db_object.is_opinion:
            update_params["sha_public"] = None
            update_params["sha_picked"] = None
            update_params["pubdate"] = None

        db_object.update(**update_params)
        content_unpublished.send(
            sender=db_object.__class__, instance=db_object, target=db_object.__class__, moderator=moderator
        )
        # clean files
        old_path = public_version.get_prod_path()
        public_version.content.update(public_version=None, sha_public=None)
        if path.exists(old_path):
            shutil.rmtree(old_path)
        return True

    return False


def close_article_beta(db_object, versioned, user, request=None):
    """
    Close forum topic of an article if the artcle was in beta.
    :param db_object: the article
    :type db_object: zds.tutorialv2.models.database.PublishableContent
    :param versioned: the public version of article, used to pupulate closing post
    :type versioned: zds.tutorialv2.models.versioned.VersionedContent
    :param user: the current user
    :param request: the current request
    """
    if db_object.type == "ARTICLE":
        db_object.sha_beta = None
        topic = db_object.beta_topic
        if topic is not None and not topic.is_locked:
            msg_post = render_to_string("tutorialv2/messages/beta_desactivate.md", {"content": versioned})
            send_post(request, topic, user, msg_post)
            lock_topic(topic)


def save_validation_state(
    db_object,
    is_update,
    published: PublishedContent,
    validation,
    versioned,
    source="",
    is_major=False,
    user=None,
    request=None,
    comment="",
):
    """
    Save validation after publication, changes its status to ACCEPT
    :param db_object:  the content
    :type db_object: zds.tutorialv2.models.database.PublishableContent
    :param is_update: marks if the publication is an update or a new/major publication
    :param published: the PublishedContent instance
    :param validation: the related validation
    :param versioned:  the VersionedContent related to the public sha
    :param source: the optional cannonical link
    :param is_major: marks a major publication (first one, or new parts for example)
    :param user: validating user
    :param request: current request to get hats, and send error messages if needed
    """
    db_object.sha_public = validation.version
    db_object.source = source
    db_object.sha_validation = None
    db_object.public_version = published
    if is_major or not is_update or db_object.pubdate is None:
        db_object.pubdate = datetime.now()
        db_object.is_obsolete = False

    # close beta if is an article
    close_article_beta(db_object, versioned, user=user, request=request)
    db_object.save()
    # save validation object
    validation.comment_validator = comment
    validation.status = "ACCEPT"
    validation.date_validation = datetime.now()
    validation.save()
