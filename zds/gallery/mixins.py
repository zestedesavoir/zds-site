import datetime

from uuslug import slugify

from zds.gallery.models import Gallery, UserGallery, GALLERY_WRITE, GALLERY_READ, Image
from zds.tutorialv2.models.database import PublishableContent


class GalleryMixin:
    gallery = None
    users_and_permissions = []

    def get_gallery(self, pk, slug=None):
        queryset = Gallery.objects.filter(pk=pk)
        if slug is not None:
            queryset = queryset.filter(slug=slug)

        self.gallery = queryset.get()
        self.users_and_permissions = self.gallery.get_users_and_permissions()

        return self.gallery

    def has_access_to_gallery(self, user, must_write=False):
        if user.pk in self.users_and_permissions:
            return True if not must_write else self.users_and_permissions[user.pk]['write']
        return False

    def linked_content(self):
        try:
            return PublishableContent.objects.filter(gallery=self.gallery).get()
        except PublishableContent.DoesNotExist:
            return None


class GalleryCreateMixin(GalleryMixin):

    def perform_create(self, title, user, subtitle=''):
        gallery = Gallery(title=title)
        gallery.subtitle = subtitle
        gallery.slug = slugify(title)
        gallery.pubdate = datetime.datetime.now()
        gallery.save()

        user_gallery = UserGallery(gallery=gallery, user=user, mode=GALLERY_WRITE)
        user_gallery.save()

        self.gallery = gallery
        self.users_and_permissions = {user.pk: {'read': True, 'write': True}}


class NoMoreUserWithWriteIfLeave(Exception):
    pass


class GalleryUpdateOrDeleteMixin(GalleryMixin):
    def perform_update(self, data):
        """Update gallery information"""
        if 'title' in data:
            self.gallery.title = data.get('title')
            self.gallery.slug = slugify(self.gallery.title)
        if 'subtitle' in data:
            self.gallery.subtitle = data.get('subtitle')

        self.gallery.save()

    def perform_update_user(self, user, can_write=False, allow_modify=True):
        """Add user to gallery or update its permissions"""
        mode = GALLERY_WRITE if can_write else GALLERY_READ
        if user.pk not in self.users_and_permissions:
            user_gallery = UserGallery(
                user=user, gallery=self.gallery, mode=mode)
            user_gallery.save()
            self.users_and_permissions[user.pk] = {'read': True, 'write': can_write}
        elif allow_modify:
            if self.users_and_permissions[user.pk]['write'] != can_write:
                user_gallery = UserGallery.objects.filter(user=user, gallery=self.gallery).get()
                user_gallery.mode = mode
                user_gallery.save()
                self.users_and_permissions[user.pk]['write'] = can_write

    def perform_delete(self):
        """Delete gallery"""
        UserGallery.objects.filter(gallery=self.gallery).delete()
        self.gallery.delete()

    def perform_leave(self, user):
        """Remove user.
        Return True if the gallery was deleted, False otherwise.
        Fail if the user was the last with write permissions on the gallery.
        """
        still_one_user_with_write = False
        for user_pk, user_perms in self.users_and_permissions.items():
            if user_pk == user.pk:
                continue
            if user_perms['write']:
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
        self.image = Image.objects.filter(pk=pk, gallery=self.gallery).get()

        return self.image
