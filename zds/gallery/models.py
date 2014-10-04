# coding: utf-8

import os
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from easy_thumbnails.fields import ThumbnailerImageField
from zds.settings import MEDIA_ROOT

GALLERY_WRITE = 'W'
GALLERY_READ = 'R'


def image_path(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('galleries', str(instance.gallery.pk), filename)


class UserGallery(models.Model):

    class Meta:
        verbose_name = "Galeries de l'utilisateur"
        verbose_name_plural = "Galeries de l'utilisateur"

    user = models.ForeignKey(User, verbose_name=('Membre'), db_index=True)
    gallery = models.ForeignKey('Gallery', verbose_name=('Galerie'), db_index=True)
    MODE_CHOICES = (
        (GALLERY_READ, 'Lecture'),
        (GALLERY_WRITE, 'Ecriture')
    )
    mode = models.CharField(max_length=1, choices=MODE_CHOICES, default=GALLERY_READ)

    def __unicode__(self):
        """Textual form of an User Gallery."""
        return u'Galerie "{0}" envoye par {1}'.format(self.gallery,
                                                      self.user)

    def is_write(self):
        return self.mode == GALLERY_WRITE

    def is_read(self):
        return self.mode == GALLERY_READ

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
    physical = ThumbnailerImageField(upload_to=image_path)
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


@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes image from filesystem when corresponding object is deleted."""
    if instance.physical:
        if os.path.isfile(instance.physical.path):
            os.remove(instance.physical.path)


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

    def get_gallery_path(self):
        """get the physical path to this gallery root"""
        return os.path.join(MEDIA_ROOT, 'galleries', str(self.pk))

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


@receiver(models.signals.post_delete, sender=Gallery)
def auto_delete_image_on_delete(sender, instance, **kwargs):
    """Deletes image from filesystem when corresponding object is deleted."""
    for image in instance.get_images():
        image.delete()
