# coding: utf-8

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.gallery.factories import ImageFactory, GalleryFactory, UserGalleryFactory
from zds.gallery.models import Image, Gallery
from zds.member.factories import ProfileFactory
from zds.utils import slugify

import os


class GalleryTests(TestCase):

    def setUp(self):

        self.profile = ProfileFactory()

        login_check = self.client.login(
            username=self.profile.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

    def test_create_gallery(self):
        """To test user create gallery."""

        self.assertEqual(Gallery.objects.count(), 0)

        result = self.client.post(
            reverse('zds.gallery.views.new_gallery'),
            {'title': u"Ma galerie super trop cool",
             'subtitle': u"La galerie de ma galerie est ma galerie"},
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Gallery.objects.count(), 1)

    def test_create_gallery_empty_title(self):
        """To test user create gallery with an empty title."""

        self.assertEqual(Gallery.objects.count(), 0)

        result = self.client.post(
            reverse('zds.gallery.views.new_gallery'),
            {'subtitle': u"La galerie de ma galerie est ma galerie"},
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Gallery.objects.count(), 0)

    def test_url_gallery(self):
        """To test url of gallery."""

        gallery1 = GalleryFactory()
        gallery2 = GalleryFactory()
        GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=gallery2)

        result = self.client.get(
            reverse(
                'zds.gallery.views.gallery_details',
                args=[
                    gallery2.pk,
                    slugify(gallery2.title)]),
            follow=True)

        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.gallery.views.gallery_details',
                args=[
                    gallery1.pk,
                    slugify(gallery1.title)]),
            follow=True)

        self.assertEqual(result.status_code, 403)

    def test_url_list_gallery(self):
        """To test url list of galleries."""

        GalleryFactory()
        gallery2 = GalleryFactory()
        GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=gallery2)

        result = self.client.get(
            reverse(
                'zds.gallery.views.gallery_list'),
            follow=True)

        self.assertEqual(result.status_code, 200)


class ImageTests(TestCase):

    def setUp(self):

        self.profile = ProfileFactory()
        self.gallery = GalleryFactory()
        self.ug = UserGalleryFactory(user=self.profile.user, gallery=self.gallery)

        login_check = self.client.login(
            username=self.profile.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

    def test_create_image(self):
        """To test user create image in gallery."""

        self.assertEqual(Image.objects.count(), 0)

        result = self.client.post(
            reverse('zds.gallery.views.new_image',
                    args=[self.gallery.pk]),
            {'title': u"Mon image super trop cool",
             'legend': u"Légende de ma galerie",
             'physical': open(
                       os.path.join(
                           settings.SITE_ROOT,
                           'fixtures',
                           'logo.png',
                       ), 'r')},
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Image.objects.count(), 1)

    def test_url_image(self):
        """To test url of image."""
        image1 = ImageFactory(gallery=self.gallery)
        result = self.client.get(
            reverse(
                'zds.gallery.views.edit_image',
                args=[
                    self.gallery.pk,
                    image1.pk]),
            follow=False)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(Image.objects.count(), 1)
