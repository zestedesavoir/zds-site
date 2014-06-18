# coding: utf-8

from cStringIO import StringIO
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.dispatch import receiver
import os
import string
import uuid

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from PIL import Image as PILImage


IMAGE_THUMB_MAX_WIDTH = 128
IMAGE_THUMB_MAX_HEIGHT = 128
IMAGE_MEDIUM_MAX_WIDTH = 400
IMAGE_MEDIUM_MAX_HEIGHT = 300


def image_path(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join(
        'galleries', 'normal', str(
            instance.gallery.pk), filename)


def image_path_thumb(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join(
        'galleries', 'thumb', str(
            instance.gallery.pk), filename)


def image_path_medium(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join(
        'galleries', 'medium', str(
            instance.gallery.pk), filename)


class UserGallery(models.Model):

    class Meta:
        verbose_name = "Galeries de l'utilisateur"
        verbose_name_plural = "Galeries de l'utilisateur"

    user = models.ForeignKey(User, verbose_name=('Membre'), db_index=True)
    gallery = models.ForeignKey('Gallery', verbose_name=('Galerie'), db_index=True)
    MODE_CHOICES = (
        ('R', 'Lecture'),
        ('W', 'Ecriture')
    )
    mode = models.CharField(max_length=1, choices=MODE_CHOICES, default='R')

    def __unicode__(self):
        """Textual form of an User Gallery."""
        return u'Galerie "{0}" envoye par {1}'.format(self.gallery,
                                                      self.user)

    def is_write(self):
        return self.mode == 'W'

    def is_read(self):
        return self.mode == 'R'

    def get_images(self):
        return Image.objects.all()\
            .filter(gallery=self.gallery)\
            .order_by('update')

    def get_gallery(self, user):
        return Gallery.objects.all()\
            .filter(pk=self.gallery.pk)


class Image(models.Model):

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

    gallery = models.ForeignKey('Gallery', verbose_name=('Galerie'), db_index=True)
    title = models.CharField('Titre', max_length=80, null=True, blank=True)
    slug = models.SlugField(max_length=80)
    physical = models.ImageField(upload_to=image_path)
    thumb = models.ImageField(
        upload_to=image_path_thumb,
        null=True,
        blank=True)
    medium = models.ImageField(
        upload_to=image_path_medium,
        null=True,
        blank=True)
    legend = models.CharField('Légende', max_length=80, null=True, blank=True)
    pubdate = models.DateTimeField('Date de création', auto_now_add=True, db_index=True)
    update = models.DateTimeField(
        'Date de modification', null=True, blank=True)

    def __unicode__(self):
        """Textual form of an Image."""
        return self.slug

    def get_absolute_url(self):
        return '{0}/{1}'.format(settings.MEDIA_URL, self.physical)

    def get_extension(self):
        return os.path.splitext(self.physical.name)[1][1:]

    def save(
        self,
        force_update=False,
        force_insert=False,
        thumb_size=(
            IMAGE_THUMB_MAX_WIDTH,
            IMAGE_THUMB_MAX_HEIGHT),
        medium_size=(
            IMAGE_MEDIUM_MAX_WIDTH,
            IMAGE_MEDIUM_MAX_HEIGHT), *args, **kwargs):
        if has_changed(self, 'physical') and self.physical:
            # TODO : delete old image

            image = PILImage.open(self.physical)

            if image.mode not in ('L', 'RGB', 'P', 'RGBA'):
                image = image.convert('RGB')

            # Medium
            image.thumbnail(medium_size, PILImage.ANTIALIAS)

            # save the thumbnail to memory
            temp_handle = StringIO()
            image.save(temp_handle, 'png')
            temp_handle.seek(0)  # rewind the file

            # save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(self.physical.name)[-1],
                                     temp_handle.read(),
                                     content_type='image/png')
            self.medium.save(suf.name + '.png', suf, save=False)

            # Thumbnail
            image.thumbnail(thumb_size, PILImage.ANTIALIAS)

            # save the thumbnail to memory
            temp_handle = StringIO()
            image.save(temp_handle, 'png')
            temp_handle.seek(0)  # rewind the file

            # save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(self.physical.name)[-1],
                                     temp_handle.read(),
                                     content_type='image/png')
            self.thumb.save(suf.name + '.png', suf, save=False)

            # save the image object
            super(Image, self).save(force_update, force_insert)
        else:
            super(Image, self).save()


def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model May be used in a
    model.save() method."""
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old

# These two auto-delete files from filesystem when they are unneeded:


@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes image from filesystem when corresponding object is deleted."""
    if instance.physical:
        if os.path.isfile(instance.physical.path):
            os.remove(instance.physical.path)
    if instance.medium:
        if os.path.isfile(instance.medium.path):
            os.remove(instance.medium.path)
    if instance.thumb:
        if os.path.isfile(instance.thumb.path):
            os.remove(instance.thumb.path)


class Gallery(models.Model):

    class Meta:
        verbose_name = "Galerie"
        verbose_name_plural = "Galeries"

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous titre', max_length=200)
    slug = models.SlugField(max_length=80)
    pubdate = models.DateTimeField('Date de création', auto_now_add=True, db_index=True)
    update = models.DateTimeField(
        'Date de modification', null=True, blank=True)

    def __unicode__(self):
        """Textual form of an Gallery."""
        return self.title

    def get_absolute_url(self):
        return reverse('zds.gallery.views.gallery_details',
                       args=[self.pk, self.slug])

    # TODO rename function to get_users_galleries
    def get_users(self):
        return UserGallery.objects.all()\
            .filter(gallery=self)

    def get_images(self):
        return Image.objects.all()\
            .filter(gallery=self)\
            .order_by('pubdate')

    def get_last_image(self):
        return Image.objects.all()\
            .filter(gallery=self)\
            .order_by('-pubdate')[0]
