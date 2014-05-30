# coding: utf-8

import os

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from zds.gallery.forms import GalleryForm, UserGalleryForm, ImageForm, ImageAsAvatarForm
from zds.member.factories import ProfileFactory
from zds import settings


class GalleryFormTest(TestCase):

    def test_gallery_form(self):
        data = {
            'title': 'Test Title',
            'subtitle': 'Test Subtitle'
        }
        form = GalleryForm(data=data)

        self.assertTrue(form.is_valid())

    def test_gallery_form_empty_title(self):
        """ Test when title contains only whitespace """
        data = {
            'title': ' ',
            'subtitle': 'Test Subtitle'
        }
        form = GalleryForm(data=data)

        self.assertFalse(form.is_valid())

    def test_gallery_form_no_title(self):
        data = {
            'subtitle': 'Test Subtitle'
        }
        form = GalleryForm(data=data)

        self.assertFalse(form.is_valid())


class UserGalleryFormTest(TestCase):

    def setUp(self):
        self.profile = ProfileFactory()

    def test_user_gallery_form(self):
        data = {
            'user': self.profile,
            'mode': 'R'
        }
        form = UserGalleryForm(data=data)

        self.assertTrue(form.is_valid())

    def test_user_gallery_form_noexist_user(self):
        data = {
            'user': 'hello',
            'mode': 'W'
        }
        form = UserGalleryForm(data=data)

        self.assertFalse(form.is_valid())


class ImageFormTest(TestCase):

    def test_image_form(self):
        upload_file = open(os.path.join(settings.SITE_ROOT, 'fixtures', 'logo.png'), 'r')

        data = {
            'title': 'Test Image',
            'legend': 'Test Legend',
        }

        files = {
            'physical': SimpleUploadedFile(upload_file.name, upload_file.read())
        }
        form = ImageForm(data, files)

        self.assertTrue(form.is_valid())
        upload_file.close()


class ImageAsAvatarFormTest(TestCase):

    def test_image_as_avatar_form(self):
        form = ImageAsAvatarForm()

        self.assertFalse(form.is_bound)
