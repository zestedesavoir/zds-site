import os
from uuid import uuid4
from shutil import rmtree

from easy_thumbnails.fields import ThumbnailerImageField
from easy_thumbnails.files import get_thumbnailer

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


# Models settings
GALLERY_WRITE = 'W'
GALLERY_READ = 'R'


def image_path(instance, filename):
    """
    Get the local filesystem path of the uploaded image. This function is used in models.

    :param instance: an instance of the model where the ImageField is defined
    :type instance: str
    :param filename: the filename that was originally given to the file
    :type filename: str
    :return: local filesystem path of the uploaded image
    :rtype: unicode
    """
    ext = filename.split('.')[-1].lower()
    filename = '{0}.{1}'.format(str(uuid4()), ext)

    return os.path.join('galleries', str(instance.gallery.pk), filename)


class UserGallery(models.Model):
    """A gallery of images created by a user."""

    class Meta:
        verbose_name = _('Galeries de l\'utilisateur')
        verbose_name_plural = _('Galeries de l\'utilisateur')

    MODE_CHOICES = (
        (GALLERY_READ, _('Lecture')),
        (GALLERY_WRITE, _('Écriture'))
    )

    user = models.ForeignKey(User, verbose_name=_('Membre'), db_index=True)
    gallery = models.ForeignKey('Gallery', verbose_name=_('Galerie'), db_index=True)
    mode = models.CharField(max_length=1, choices=MODE_CHOICES, default=GALLERY_READ)

    def __str__(self):
        """Human-readable representation of the UserGallery model.

        :return: UserGalley description
        :rtype: unicode
        """
        return _('Galerie « {0} » de {1}').format(self.gallery, self.user)

    def can_write(self):
        """Check if user can write in the gallery.

        :return: True if user can write in the gallery
        :rtype: bool
        """
        return self.mode == GALLERY_WRITE

    def can_read(self):
        """Check if user can read in the gallery.

        :return: True if user can read in the gallery
        :rtype: bool
        """
        return self.mode == GALLERY_READ

    def get_images(self):
        """Get all images in the gallery.

        :return: all images in the gallery
        :rtype: QuerySet
        """
        return Image.objects.filter(gallery=self.gallery).order_by('update').all()


class Image(models.Model):
    """Represent an image in database"""

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

    gallery = models.ForeignKey('Gallery', verbose_name=_('Galerie'), db_index=True)
    title = models.CharField(_('Titre'), max_length=80)
    slug = models.SlugField(max_length=80)
    physical = ThumbnailerImageField(upload_to=image_path, max_length=200)
    legend = models.CharField(_('Légende'), max_length=80, null=True, blank=True)
    pubdate = models.DateTimeField(_('Date de création'), auto_now_add=True, db_index=True)
    update = models.DateTimeField(_('Date de modification'), null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)

    def __str__(self):
        """Human-readable representation of the Image model.

        :return: Image slug
        :rtype: unicode
        """
        return self.slug

    def get_absolute_url(self):
        """URL of a single Image.

        :return: Image object URL
        :rtype: str
        """
        return '{0}/{1}'.format(settings.MEDIA_URL, self.physical)

    def get_extension(self):
        """Get the extension of an image (used in tests).

        :return: the extension of the image
        :rtype: unicode
        """
        return os.path.splitext(self.physical.name)[1][1:]


@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes image from filesystem when corresponding object is deleted.

    :return: nothing
    :rtype: None
    """
    if instance.physical:
        thumbmanager = get_thumbnailer(instance.physical)
        thumbmanager.delete(save=False)


class Gallery(models.Model):

    class Meta:
        verbose_name = _('Galerie')
        verbose_name_plural = _('Galeries')

    title = models.CharField(_('Titre'), max_length=80)
    subtitle = models.CharField(_('Sous titre'), max_length=200, blank=True)
    slug = models.SlugField(max_length=80)
    pubdate = models.DateTimeField(_('Date de création'), auto_now_add=True, db_index=True)
    update = models.DateTimeField(_('Date de modification'), null=True, blank=True)

    def __str__(self):
        """Human-readable representation of the Gallery model.

        :return: Gallery title
        :rtype: unicode
        """
        return self.title

    def get_absolute_url(self):
        """URL of a single Gallery.

        :return: Gallery object URL
        :rtype: str
        """
        return reverse('gallery-details', args=[self.pk, self.slug])

    def get_gallery_path(self):
        """Get the filesystem path to this gallery root.

        :return: filesystem path to this gallery root
        :rtype: unicode
        """
        return os.path.join(settings.MEDIA_ROOT, 'galleries', str(self.pk))

    def get_linked_users(self):
        """Get all the linked users for this gallery whatever their rights

        :return: all the linked users for this gallery
        :rtype: QuerySet
        """
        return UserGallery.objects.filter(gallery=self).all()

    def get_images(self):
        """Get all images in the gallery, ordered by publication date.

        :return: all images in the gallery
        :rtype: QuerySet
        """
        return Image.objects.filter(gallery=self).order_by('pubdate').all()

    def get_last_image(self):
        """Get the last image added in the gallery.

        :return: last image added in the gallery
        :rtype: Image object
        """
        return Image.objects.filter(gallery=self).last()


@receiver(models.signals.post_delete, sender=Gallery)
def auto_delete_image_on_delete(sender, instance, **kwargs):
    """Deletes image from filesystem when corresponding object is deleted.

    :return: nothing
    :rtype: None
    """
    # Remove all pictures of the gallery
    for image in instance.get_images():
        image.delete()
    # Remove the folder of the gallery if it exists
    if os.path.isdir(instance.get_gallery_path()):
        rmtree(instance.get_gallery_path())
