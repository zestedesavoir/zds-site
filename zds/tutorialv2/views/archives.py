import os
import re
import shutil
import tempfile
import time
import zipfile
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from easy_thumbnails.files import get_thumbnailer
from PIL import Image as ImagePIL

from zds import json_handler
from zds.gallery.models import Gallery, Image
from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.forms import ImportContentForm, ImportNewContentForm
from zds.tutorialv2.mixins import SingleContentDownloadViewMixin, SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.versioned import Container, Extract
from zds.tutorialv2.utils import (
    BadArchiveError,
    BadManifestError,
    default_slug_pool,
    get_content_from_json,
    init_new_repo,
)
from zds.utils.uuslug_wrapper import slugify
from zds.utils.validators import InvalidSlugError


class DownloadContent(LoginRequiredMixin, SingleContentDownloadViewMixin):
    """
    Download a zip archive with all the content of the repository directory
    """

    mimetype = "application/zip"
    must_be_author = False  # other user can download archive

    @staticmethod
    def insert_into_zip(zip_file, git_tree):
        """Recursively add file into zip

        :param zip_file: a ``zipfile`` object (with writing permissions)
        :param git_tree: Git tree (from ``repository.commit(sha).tree``)
        """
        for blob in git_tree.blobs:  # first, add files :
            zip_file.writestr(blob.path, blob.data_stream.read())
        if git_tree.trees:  # then, recursively add dirs :
            for subtree in git_tree.trees:
                DownloadContent.insert_into_zip(zip_file, subtree)

    def get_contents(self):
        """get the zip file stream

        :return: a zip file
        :rtype: byte
        """
        versioned = self.versioned_object

        # create and fill zip
        path = self.object.get_repo_path()
        zip_path = path + self.get_filename()
        zip_file = zipfile.ZipFile(zip_path, "w")
        self.insert_into_zip(zip_file, versioned.repository.commit(versioned.current_version).tree)
        zip_file.close()

        # return content
        response = open(zip_path, "rb").read()
        os.remove(zip_path)
        return response

    def get_filename(self):
        return self.get_object().slug + ".zip"


class UpdateContentWithArchive(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """Update a content using an archive"""

    template_name = "tutorialv2/import/content.html"
    form_class = ImportContentForm

    @staticmethod
    def walk_container(container):
        """Iterator that yield each file path in a Container

        :param container: the container
        :type container: Container
        :rtype: collections.Iterable[str]
        """

        if container.introduction:
            yield container.introduction
        if container.conclusion:
            yield container.conclusion

        for child in container.children:
            if isinstance(child, Container):
                yield from UpdateContentWithArchive.walk_container(child)
            else:
                yield child.text

    @staticmethod
    def walk_content(versioned):
        """Iterator that yield each files in a VersionedContent

        :param versioned: the content
        :type versioned: VersionedContent
        :rtype: collections.Iterable[str]
        """

        yield from UpdateContentWithArchive.walk_container(versioned)

    @staticmethod
    def extract_content_from_zip(zip_archive):
        """Check if the data in the zip file are coherent

        :param zip_archive: the zip archive to analyze
        :type zip_archive: zipfile.ZipFile
        :raise BadArchiveError: if something is wrong in the archive
        :return: the content in the archive
        :rtype: VersionedContent
        """

        try:
            manifest = str(zip_archive.read("manifest.json"), "utf-8")
        except KeyError:
            raise BadArchiveError(_("Cette archive ne contient pas de fichier manifest.json."))
        except UnicodeDecodeError:
            raise BadArchiveError(_("L'encodage du manifest.json n'est pas de l'UTF-8."))

        # is the manifest ok ?
        try:
            json_ = json_handler.loads(manifest)
        except ValueError:
            raise BadArchiveError(
                _(
                    "Une erreur est survenue durant la lecture du manifest, "
                    "vérifiez qu'il s'agit de JSON correctement formaté."
                )
            )
        try:
            versioned = get_content_from_json(
                json_, None, "", max_title_len=PublishableContent._meta.get_field("title").max_length
            )
        except BadManifestError as e:
            raise BadArchiveError(e.message)
        except InvalidSlugError as e:
            e1 = _('Le slug "{}" est invalide').format(e)
            e2 = ""
            if e.had_source:
                e2 = _(' (slug généré à partir de "{}")').format(e.source)
            raise BadArchiveError(_("{}{} !").format(e1, e2))
        except Exception as e:
            raise BadArchiveError(_("Une erreur est survenue lors de la lecture de l'archive : {}.").format(e))

        # is there everything in the archive ?
        for f in UpdateContentWithArchive.walk_content(versioned):
            try:
                zip_archive.getinfo(f)
            except KeyError:
                raise BadArchiveError(_("Le fichier '{}' n'existe pas dans l'archive.").format(f))

        return versioned

    @staticmethod
    def update_from_new_version_in_zip(copy_to, copy_from, zip_file):
        """Copy the information from ``new_container`` into ``copy_to``.
        This function correct path for file if necessary

        :param copy_to: container that to copy to
        :type copy_to: Container
        :param copy_from: copy from container
        :type copy_from: Container
        :param zip_file: zip file that contain the files
        :type zip_file: zipfile.ZipFile
        """

        for child in copy_from.children:
            if isinstance(child, Container):
                introduction = ""
                conclusion = ""

                if child.introduction:
                    try:
                        introduction = str(zip_file.read(child.introduction), "utf-8")
                    except UnicodeDecodeError:
                        raise BadArchiveError(_(f"Le fichier « {child.introduction} » n'est pas encodé en UTF-8"))
                if child.conclusion:
                    try:
                        conclusion = str(zip_file.read(child.conclusion), "utf-8")
                    except UnicodeDecodeError:
                        raise BadArchiveError(_(f"Le fichier « {child.conclusion} » n'est pas encodé en UTF-8"))

                copy_to.repo_add_container(
                    child.title,
                    introduction,
                    conclusion,
                    do_commit=False,
                    slug=child.slug,
                    ready_to_publish=child.ready_to_publish,
                )
                UpdateContentWithArchive.update_from_new_version_in_zip(copy_to.children[-1], child, zip_file)

            elif isinstance(child, Extract):
                try:
                    text = str(zip_file.read(child.text), "utf-8")
                except UnicodeDecodeError:
                    raise BadArchiveError(_(f"Le fichier « {child.text} » n'est pas encodé en UTF-8"))

                copy_to.repo_add_extract(child.title, text, do_commit=False, slug=child.slug)

    @staticmethod
    def use_images_from_archive(request, zip_file, versioned_content, gallery):
        """Extract image from a gallery and then translate the ``![.+](prefix:filename)`` into the final image we want.
        The ``prefix`` is defined into the settings.
        Note that this function does not perform any commit.

        :param zip_file: ZIP archive
        :type zip_file: zipfile.ZipFile
        :param versioned_content: content
        :type versioned_content: VersionedContent
        :param gallery: gallery of image
        :type gallery: Gallery
        """
        translation_dic = {}

        # create a temporary directory:
        temp = os.path.join(tempfile.gettempdir(), str(time.time()))
        if not os.path.exists(temp):
            os.makedirs(temp)

        for image_path in zip_file.namelist():
            image_basename = os.path.basename(image_path)

            if not image_basename.strip():  # don't deal with directory
                continue

            temp_image_path = os.path.abspath(os.path.join(temp, image_basename))

            # create a temporary file for the image
            f_im = open(temp_image_path, "wb")
            f_im.write(zip_file.read(image_path))
            f_im.close()

            # if it's not an image, pass
            try:
                ImagePIL.open(temp_image_path)
            except OSError:
                continue

            # if size is too large, pass
            if os.stat(temp_image_path).st_size > settings.ZDS_APP["gallery"]["image_max_size"]:
                messages.error(
                    request,
                    _(
                        'Votre image "{}" est beaucoup trop lourde, réduisez sa taille à moins de {:.0f}'
                        "Kio avant de l'envoyer."
                    ).format(image_path, settings.ZDS_APP["gallery"]["image_max_size"] / 1024),
                )
                continue

            # create picture in database:
            pic = Image()
            pic.gallery = gallery
            pic.title = image_basename
            pic.slug = slugify(image_basename)
            pic.physical = get_thumbnailer(open(temp_image_path, "rb"), relative_name=temp_image_path)
            pic.pubdate = datetime.now()
            pic.save()

            translation_dic[image_path] = settings.ZDS_APP["site"]["url"] + pic.physical.url

            # finally, remove image
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

        zip_file.close()
        if os.path.exists(temp):
            shutil.rmtree(temp)

        # then, modify each extracts
        image_regex = re.compile(
            r"((?P<start>!\[.*?\]\()"
            + settings.ZDS_APP["content"]["import_image_prefix"]
            + r":(?P<path>.*?)(?P<end>\)))"
        )

        for element in versioned_content.traverse(only_container=False):
            if isinstance(element, Container):
                introduction = element.get_introduction()
                introduction = image_regex.sub(
                    lambda g: UpdateContentWithArchive.update_image_link(g, translation_dic), introduction
                )

                conclusion = element.get_conclusion()
                conclusion = image_regex.sub(
                    lambda g: UpdateContentWithArchive.update_image_link(g, translation_dic), conclusion
                )
                element.repo_update(element.title, introduction, conclusion, do_commit=False)
            else:
                section_text = element.get_text()
                section_text = image_regex.sub(
                    lambda g: UpdateContentWithArchive.update_image_link(g, translation_dic), section_text
                )

                element.repo_update(element.title, section_text, do_commit=False)

    @staticmethod
    def update_image_link(group, translation_dic):
        """callback function for the transformation of ``image:xxx`` to the right path in gallery

        :param group: matching object
        :type group: re.MatchObject
        :param translation_dic: image to link into gallery dictionary
        :type translation_dic: dict
        :return: updated link
        :rtype: str
        """
        start, image, end = group.group("start"), group.group("path"), group.group("end")

        if image in translation_dic:
            return start + translation_dic[image] + end
        else:
            return start + settings.ZDS_APP["content"]["import_image_prefix"] + ":" + image + end

    def form_valid(self, form):
        versioned = self.versioned_object

        if self.request.FILES["archive"]:
            try:
                zfile = zipfile.ZipFile(self.request.FILES["archive"], "r")
            except zipfile.BadZipfile:
                messages.error(self.request, _("Cette archive n'est pas au format ZIP."))
                return super().form_invalid(form)

            try:
                new_version = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super().form_invalid(form)
            else:
                # Warn the user if the license has been changed
                manifest = json_handler.loads(str(zfile.read("manifest.json"), "utf-8"))
                if new_version.licence and "licence" in manifest and manifest["licence"] != new_version.licence.code:
                    messages.info(
                        self.request, _("la licence « {} » a été appliquée.").format(new_version.licence.code)
                    )

                # first, update DB object (in order to get a new slug if needed)
                title_is_changed = self.object.title != new_version.title
                self.object.title = new_version.title
                self.object.description = new_version.description
                self.object.licence = new_version.licence
                self.object.type = new_version.type  # change of type is then allowed !!
                self.object.save(force_slug_update=title_is_changed)

                new_version.slug = self.object.slug  # new slug if any !!

                # ok, then, let's do the import. First, remove everything in the repository
                while True:
                    if versioned.children:
                        versioned.children[0].repo_delete(do_commit=False)
                    else:
                        break  # this weird construction ensure that everything is removed

                versioned.slug_pool = default_slug_pool()  # slug pool to its initial value (to avoid weird stuffs)

                # start by copying extra information
                self.object.insert_data_in_versioned(versioned)  # better have a clean version of those one
                versioned.description = new_version.description
                versioned.type = new_version.type
                versioned.licence = new_version.licence

                # update container (and repo)
                introduction = ""
                conclusion = ""

                if new_version.introduction:
                    introduction = str(zfile.read(new_version.introduction), "utf-8")
                if new_version.conclusion:
                    conclusion = str(zfile.read(new_version.conclusion), "utf-8")

                versioned.ready_to_publish = new_version.ready_to_publish
                versioned.repo_update_top_container(
                    new_version.title, new_version.slug, introduction, conclusion, do_commit=False
                )

                # then do the dirty job:
                try:
                    UpdateContentWithArchive.update_from_new_version_in_zip(versioned, new_version, zfile)
                except BadArchiveError as e:
                    versioned.repository.index.reset()
                    messages.error(self.request, e.message)
                    return super().form_invalid(form)

                # and end up by a commit !!
                commit_message = form.cleaned_data["msg_commit"]

                if not commit_message:
                    commit_message = _("Importation d'une archive contenant « {} ».").format(new_version.title)

                sha = versioned.commit_changes(commit_message)

                # now, use the images from the archive if provided. To work, this HAVE TO happen after commiting files !
                if "image_archive" in self.request.FILES:
                    try:
                        zfile = zipfile.ZipFile(self.request.FILES["image_archive"], "r")
                    except zipfile.BadZipfile:
                        messages.error(self.request, _("L'archive contenant les images n'est pas au format ZIP."))
                        return self.form_invalid(form)

                    UpdateContentWithArchive.use_images_from_archive(
                        self.request, zfile, versioned, self.object.gallery
                    )

                    commit_message = _("Utilisation des images de l'archive pour « {} »").format(new_version.title)
                    sha = versioned.commit_changes(commit_message)  # another commit

                # of course, need to update sha
                self.object.sha_draft = sha
                self.object.update_date = datetime.now()
                self.object.save()

                self.success_url = reverse("content:view", args=[versioned.pk, versioned.slug])

        return super().form_valid(form)


class CreateContentFromArchive(LoggedWithReadWriteHability, FormView):
    """Create a content using an archive"""

    form_class = ImportNewContentForm
    template_name = "tutorialv2/import/content-new.html"
    object = None

    def form_valid(self, form):
        if self.request.FILES["archive"]:
            try:
                zfile = zipfile.ZipFile(self.request.FILES["archive"], "r")
            except zipfile.BadZipfile:
                messages.error(self.request, _("Cette archive n'est pas au format ZIP."))
                return self.form_invalid(form)

            try:
                new_content = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super().form_invalid(form)
            except KeyError as e:
                messages.error(self.request, _(e.message + " n'est pas correctement renseigné."))
                return super().form_invalid(form)
            else:
                # Warn the user if the license has been changed
                manifest = json_handler.loads(str(zfile.read("manifest.json"), "utf-8"))
                if new_content.licence and "licence" in manifest and manifest["licence"] != new_content.licence.code:
                    messages.info(self.request, _(f"la licence « {new_content.licence.code} » a été appliquée."))

                # first, create DB object (in order to get a slug)
                self.object = PublishableContent()
                self.object.title = new_content.title
                self.object.description = new_content.description
                self.object.licence = new_content.licence
                self.object.type = new_content.type  # change of type is then allowed !!
                self.object.creation_date = datetime.now()

                self.object.save()

                new_content.slug = self.object.slug  # new slug (choosen via DB)

                # Creating the gallery
                gal = Gallery()
                gal.title = new_content.title
                gal.slug = slugify(new_content.title)
                gal.pubdate = datetime.now()
                gal.save()

                # Attach user to gallery
                self.object.gallery = gal
                self.object.save()

                # Add subcategories on tutorial
                for subcat in form.cleaned_data["subcategory"]:
                    self.object.subcategory.add(subcat)

                # We need to save the tutorial before changing its author list since it's a many-to-many relationship
                self.object.authors.add(self.request.user)
                self.object.save()
                self.object.ensure_author_gallery()
                # ok, now we can import
                introduction = ""
                conclusion = ""

                if new_content.introduction:
                    introduction = str(zfile.read(new_content.introduction), "utf-8")
                if new_content.conclusion:
                    conclusion = str(zfile.read(new_content.conclusion), "utf-8")

                commit_message = _("Création de « {} »").format(new_content.title)
                init_new_repo(self.object, introduction, conclusion, commit_message=commit_message)

                # copy all:
                versioned = self.object.load_version()
                try:
                    UpdateContentWithArchive.update_from_new_version_in_zip(versioned, new_content, zfile)
                except BadArchiveError as e:
                    self.object.delete()  # abort content creation
                    messages.error(self.request, e.message)
                    return super().form_invalid(form)

                # and end up by a commit !!
                commit_message = form.cleaned_data["msg_commit"]

                if not commit_message:
                    commit_message = _("Importation d'une archive contenant « {} »").format(new_content.title)
                versioned.slug = self.object.slug  # force slug to ensure path resolution
                sha = versioned.repo_update(
                    versioned.title,
                    versioned.get_introduction(),
                    versioned.get_conclusion(),
                    commit_message,
                    update_slug=True,
                )

                # This HAVE TO happen after commiting files (if not, content are None)
                if "image_archive" in self.request.FILES:
                    try:
                        zfile = zipfile.ZipFile(self.request.FILES["image_archive"], "r")
                    except zipfile.BadZipfile:
                        messages.error(self.request, _("L'archive contenant les images n'est pas au format ZIP."))
                        return self.form_invalid(form)

                    UpdateContentWithArchive.use_images_from_archive(
                        self.request, zfile, versioned, self.object.gallery
                    )

                    commit_message = _("Utilisation des images de l'archive pour « {} »").format(new_content.title)
                    sha = versioned.commit_changes(commit_message)  # another commit

                # of course, need to update sha
                self.object.sha_draft = sha
                self.object.update_date = datetime.now()
                self.object.save()

                self.success_url = reverse("content:view", args=[versioned.pk, versioned.slug])

        return super().form_valid(form)
