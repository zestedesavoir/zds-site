# coding: utf-8

import os

from django.test import TestCase
from django.core.urlresolvers import reverse

from zds.gallery.models import UserGallery
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.member.factories import ProfileFactory
from zds import settings


class UserGalleryTest(TestCase):

    def setUp(self):
        self.profile = ProfileFactory()
        self.gallery = GalleryFactory()
        self.image1 = ImageFactory(gallery=self.gallery)
        self.image2 = ImageFactory(gallery=self.gallery)
        self.user_gallery = UserGalleryFactory(user=self.profile.user, gallery=self.gallery)

    def tearDown(self):
        self.image1.delete()
        self.image2.delete()
        self.user_gallery.delete()
        self.gallery.delete()

    def test_unicode(self):
        result = u'Galerie "{0}" envoye par {1}'.format(self.gallery, self.profile.user)

        self.assertEqual(result, self.user_gallery.__unicode__())

    def test_is_write(self):
        self.user_gallery.mode = 'W'

        self.assertTrue(self.user_gallery.is_write())
        self.assertFalse(self.user_gallery.is_read())

    def test_is_read(self):
        self.user_gallery.mode = 'R'

        self.assertFalse(self.user_gallery.is_write())
        self.assertTrue(self.user_gallery.is_read())

    def test_get_images(self):
        self.assertEqual(2, len(self.user_gallery.get_images()))

        self.assertEqual(self.image1, self.user_gallery.get_images()[0])
        self.assertEqual(self.image2, self.user_gallery.get_images()[1])

    def test_get_gallery(self):
        gallery_results = self.user_gallery.get_gallery(self.profile.user)

        self.assertEqual(1, len(gallery_results))
        self.assertEqual(self.gallery, gallery_results[0])


class ImageTest(TestCase):

    def setUp(self):
        self.gallery = GalleryFactory()
        self.image = ImageFactory(gallery=self.gallery)

    def tearDown(self):
        self.image.delete()
        self.gallery.delete()

    def test_unicode(self):
        self.assertEqual(self.image.slug, self.image.__unicode__())

    def test_get_absolute_url(self):
        absolute_url = u'{0}/{1}'.format(settings.MEDIA_URL, self.image.physical)

        self.assertEqual(absolute_url, self.image.get_absolute_url())

    def test_get_extension(self):
        extension = os.path.splitext(self.image.physical.name)[1][1:]
        self.assertEqual(extension, self.image.get_extension())

    def test_save_image(self):
        test_image = ImageFactory(gallery=self.gallery)
        self.assertTrue(os.path.isfile(test_image.physical.path))
        self.assertTrue(os.path.isfile(test_image.medium.path))
        self.assertTrue(os.path.isfile(test_image.thumb.path))

        test_image.delete()
        self.assertFalse(os.path.isfile(test_image.physical.path))
        self.assertFalse(os.path.isfile(test_image.medium.path))
        self.assertFalse(os.path.isfile(test_image.thumb.path))


class GalleryTest(TestCase):

    def setUp(self):
        self.profile = ProfileFactory()
        self.gallery = GalleryFactory()
        self.image1 = ImageFactory(gallery=self.gallery)
        self.image2 = ImageFactory(gallery=self.gallery)
        self.user_gallery = UserGalleryFactory(user=self.profile.user, gallery=self.gallery)

    def tearDown(self):
        self.image1.delete()
        self.image2.delete()
        self.user_gallery.delete()
        self.gallery.delete()

    def test_unicode(self):
        self.assertEqual(self.gallery.title, self.gallery.__unicode__())

    def test_get_absolute_url(self):
        absolute_url = reverse('zds.gallery.views.gallery_details',
                args=[self.gallery.pk, self.gallery.slug])
        self.assertEqual(absolute_url, self.gallery.get_absolute_url())

    def test_get_users(self):
        self.assertEqual(1, len(self.gallery.get_users()))
        self.assertEqual(self.user_gallery, self.gallery.get_users()[0])

    def test_get_images(self):
        self.assertEqual(2, len(self.gallery.get_images()))
        self.assertEqual(self.image1, self.gallery.get_images()[0])
        self.assertEqual(self.image2, self.gallery.get_images()[1])

    def test_get_last_image(self):
        self.assertEqual(self.image2, self.gallery.get_last_image())

