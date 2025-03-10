import os

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from zds.gallery.tests.factories import GalleryFactory, ImageFactory, UserGalleryFactory
from zds.member.tests.factories import ProfileFactory


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

    def test_can_write(self):
        self.user_gallery.mode = "W"

        self.assertTrue(self.user_gallery.can_write())
        self.assertFalse(self.user_gallery.can_read())

    def test_can_read(self):
        self.user_gallery.mode = "R"

        self.assertFalse(self.user_gallery.can_write())
        self.assertTrue(self.user_gallery.can_read())

    def test_get_images(self):
        self.assertEqual(2, len(self.user_gallery.get_images()))

        self.assertEqual(self.image1, self.user_gallery.get_images()[0])
        self.assertEqual(self.image2, self.user_gallery.get_images()[1])


class ImageTest(TestCase):
    def setUp(self):
        self.gallery = GalleryFactory()
        self.image = ImageFactory(gallery=self.gallery)

    def tearDown(self):
        self.image.delete()
        self.gallery.delete()

    def test_get_absolute_url(self):
        absolute_url = f"{settings.MEDIA_URL}/{self.image.physical}".replace("//", "/")

        self.assertEqual(absolute_url, self.image.get_absolute_url())

    def test_get_extension(self):
        self.assertEqual("jpg", self.image.get_extension())

    def test_save_and_delete_image(self):
        test_image = ImageFactory(gallery=self.gallery)
        image_path = test_image.physical.path
        self.assertTrue(os.path.isfile(image_path))

        test_image.delete()
        self.assertFalse(os.path.isfile(image_path))


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

    def test_get_absolute_url(self):
        absolute_url = reverse("gallery:details", args=[self.gallery.pk, self.gallery.slug])
        self.assertEqual(absolute_url, self.gallery.get_absolute_url())

    def test_get_linked_users(self):
        self.assertEqual(1, len(self.gallery.get_linked_users()))
        self.assertEqual(self.user_gallery, self.gallery.get_linked_users()[0])

    def test_get_images(self):
        self.assertEqual(2, len(self.gallery.get_images()))
        self.assertEqual(self.image1, self.gallery.get_images()[0])
        self.assertEqual(self.image2, self.gallery.get_images()[1])

    def test_get_last_image(self):
        self.assertEqual(self.image2, self.gallery.get_last_image())

    def test_delete_empty_gallery(self):
        test_gallery = GalleryFactory()
        path = test_gallery.get_gallery_path()
        test_gallery.delete()
        self.assertFalse(os.path.isdir(path))

    def test_delete_gallery_with_image(self):
        test_gallery = GalleryFactory()
        test_image = ImageFactory(gallery=test_gallery)

        path_gallery = test_gallery.get_gallery_path()
        self.assertTrue(os.path.isdir(path_gallery))
        path_image = test_image.physical.path
        self.assertTrue(os.path.isfile(path_image))

        # Destroy the gallery and the image
        test_gallery.delete()
        self.assertFalse(os.path.isdir(path_gallery))
        self.assertFalse(os.path.isfile(path_image))
