import datetime
import os
import shutil
import tempfile
import zipfile

from django.conf import settings
from easy_thumbnails.files import get_thumbnailer
from PIL import Image as ImagePIL
from svglib.svglib import load_svg_file

from zds.gallery.models import GALLERY_READ, GALLERY_WRITE, Gallery, Image, UserGallery
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.uuslug_wrapper import slugify


class GalleryMixin:
    gallery = None
    users_and_permissions = []

    def get_gallery(self, pk, slug=None):
        """Get the gallery

        :param pk: pk
        :type pk: int
        :param slug: slug (optional)
        :type slug: str
        """
        queryset = Gallery.objects.annotated_gallery().filter(pk=pk)
        if slug is not None:
            queryset = queryset.filter(slug=slug)

        self.gallery = queryset.get()
        self.users_and_permissions = self.gallery.get_users_and_permissions()

        return self.gallery

    def has_access_to_gallery(self, user, must_write=False):
        """Check if user has access

        :param user:  the user
        :type user: zds.member.models.User
        :param must_write: does the user need to have write permission ?
        :type must_write: bool
        :rtype: bool
        """
        if user.pk in self.users_and_permissions:
            return True if not must_write else self.users_and_permissions[user.pk]["write"]
        return False

    def linked_content(self):
        """Is there a linked content ?

        :rtype: zds.tutorialv2.models.database.PublishableContent
        """
        if self.gallery.linked_content is None:
            return None

        try:
            return PublishableContent.objects.filter(pk=self.gallery.linked_content).get()
        except PublishableContent.DoesNotExist:
            return None


class GalleryCreateMixin(GalleryMixin):
    def perform_create(self, title, user, subtitle=""):
        """Create gallery

        :param title: title
        :type title: str
        :param user:  the user
        :type user: zds.member.models.User
        :param subtitle: subtitle
        :type subtitle: str
        :rtype: Gallery
        """
        gallery = Gallery(title=title)
        gallery.subtitle = subtitle
        gallery.slug = slugify(title)
        gallery.pubdate = datetime.datetime.now()
        gallery.save()

        user_gallery = UserGallery(gallery=gallery, user=user, mode=GALLERY_WRITE)
        user_gallery.save()

        self.gallery = gallery
        self.users_and_permissions = {user.pk: {"read": True, "write": True}}

        return self.gallery


class NoMoreUserWithWriteIfLeave(Exception):
    pass


class UserAlreadyInGallery(Exception):
    pass


class UserNotInGallery(Exception):
    pass


class GalleryUpdateOrDeleteMixin(GalleryMixin):
    def perform_update(self, data):
        """Update gallery information

        :param data: things to update
        :type data: dict
        :rtype: Gallery
        """
        if "title" in data:
            self.gallery.title = data.get("title")
            self.gallery.slug = slugify(self.gallery.title)
        if "subtitle" in data:
            self.gallery.subtitle = data.get("subtitle")

        self.gallery.save()
        return self.gallery

    def perform_add_user(self, user, can_write=False):
        """Add user to gallery

        :param user:  the user
        :type user: zds.member.models.User
        :param can_write: write permission ?
        :type can_write: bool
        """

        mode = GALLERY_WRITE if can_write else GALLERY_READ
        if user.pk not in self.users_and_permissions:
            user_gallery = UserGallery(user=user, gallery=self.gallery, mode=mode)
            user_gallery.save()
            self.users_and_permissions[user.pk] = {"read": True, "write": can_write}
            return user_gallery
        else:
            raise UserAlreadyInGallery()

    def perform_update_user(self, user, can_write=False):
        """Update its permissions

        :param user:  the user
        :type user: zds.member.models.User
        :param can_write: write permission ?
        :type can_write: bool
        """

        mode = GALLERY_WRITE if can_write else GALLERY_READ
        try:
            user_gallery = UserGallery.objects.filter(user=user, gallery=self.gallery).get()
        except UserGallery.DoesNotExist:
            raise UserNotInGallery()

        if user_gallery.mode != mode:
            user_gallery.mode = mode
            user_gallery.save()
            self.users_and_permissions[user.pk]["write"] = can_write

        return user_gallery

    def perform_delete(self):
        """Delete gallery"""
        UserGallery.objects.filter(gallery=self.gallery).delete()
        self.gallery.delete()

    def perform_leave(self, user):
        """Remove user.
        Return True if the gallery was deleted, False otherwise.
        Fail if the user was the last with write permissions on the gallery.

        :param user:  the user
        :type user: zds.member.models.User
        """
        still_one_user_with_write = False
        for user_pk, user_perms in self.users_and_permissions.items():
            if user_pk == user.pk:
                continue
            if user_perms["write"]:
                still_one_user_with_write = True
                break

        if not still_one_user_with_write:
            raise NoMoreUserWithWriteIfLeave()

        if user.pk in self.users_and_permissions:
            user_gallery = UserGallery.objects.filter(user=user, gallery=self.gallery).get()
            user_gallery.delete()
            del self.users_and_permissions[user.pk]

        if len(self.users_and_permissions) == 0:
            self.perform_delete()
            return True

        return False


class ImageMixin(GalleryMixin):
    image = None

    def get_image(self, pk):
        """Get the image

        :param pk: pk
        :type pk: int
        :rtype: zds.gallery.models.Image
        """
        self.image = Image.objects.filter(pk=pk, gallery=self.gallery).get()
        return self.image


class ImageTooLarge(Exception):
    def __init__(self, title, size):
        self.title = title
        self.size = size


class NotAnImage(Exception):
    pass


class ImageCreateMixin(ImageMixin):
    def perform_create(self, title, physical, legend=""):
        """Create a new image

        :param title: title
        :type title: str
        :param physical:
        :type physical: file
        :param legend: legend (optional)
        :type legend: str
        """
        if physical.size > settings.ZDS_APP["gallery"]["image_max_size"]:
            raise ImageTooLarge(title, physical.size)

        try:
            if not physical.name.endswith(".svg"):
                ImagePIL.open(physical)
            elif load_svg_file(physical) is None:
                raise NotAnImage(physical)
        except OSError:
            raise NotAnImage(physical)

        image = Image()
        image.gallery = self.gallery
        image.title = title

        if legend:
            image.legend = legend
        else:
            image.legend = image.title

        image.physical = physical
        image.slug = slugify(title)
        image.pubdate = datetime.datetime.now()
        image.save()

        self.image = image

        return self.image

    def perform_create_multi(self, archive):
        """Create multiple image out of an archive

        :param archive: path to the archive
        :type archive: str
        """
        temp = tempfile.mkdtemp()
        zfile = zipfile.ZipFile(archive, "r")

        error_files = []

        for i in zfile.namelist():
            info = zfile.getinfo(i)

            if info.filename[-1] == "/":  # .is_dir() in python 3.6
                continue

            basename = os.path.basename(i)
            (name, ext) = os.path.splitext(basename)

            if info.file_size > settings.ZDS_APP["gallery"]["image_max_size"]:
                error_files.append(i)
                continue

            # create file for image
            ph_temp = os.path.abspath(os.path.join(temp, basename))

            f_im = open(ph_temp, "wb")
            f_im.write(zfile.read(i))
            f_im.close()
            try:
                # create picture:
                f_im = get_thumbnailer(open(ph_temp, "rb"), relative_name=ph_temp)
                f_im.name = basename
                self.perform_create(name, f_im)
                f_im.close()
            except NotAnImage:
                error_files.append(i)
                continue
            if os.path.exists(ph_temp):
                os.remove(ph_temp)

        zfile.close()

        if os.path.exists(temp):
            shutil.rmtree(temp)

        return error_files


class ImageUpdateOrDeleteMixin(ImageMixin):
    def perform_update(self, data):
        """Update image information

        :param data: things to update
        :type data: dict
        """

        if "physical" in data:
            physical = data.get("physical")
            if physical.size > settings.ZDS_APP["gallery"]["image_max_size"]:
                raise ImageTooLarge(self.image.title, physical.size)

            try:
                if not physical.name.endswith(".svg"):
                    ImagePIL.open(physical)
                elif load_svg_file(physical) is None:
                    raise NotAnImage(physical)
            except OSError:
                raise NotAnImage(physical)

            self.image.physical = physical

        if "title" in data:
            self.image.title = data.get("title")
            self.image.slug = slugify(self.image.title)

        if "legend" in data:
            self.image.legend = data.get("legend")

        self.image.save()

        return self.image

    def perform_delete(self):
        """Delete image"""
        self.image.delete()
