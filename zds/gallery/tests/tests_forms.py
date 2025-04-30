from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from zds.gallery.forms import ArchiveImageForm, GalleryForm, ImageAsAvatarForm, ImageForm, UserGalleryForm
from zds.gallery.tests.factories import GalleryFactory
from zds.member.tests.factories import ProfileFactory


class GalleryFormTest(TestCase):
    def test_valid_gallery_form(self):
        data = {"title": "Test Title", "subtitle": "Test Subtitle"}
        form = GalleryForm(data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_gallery_form_empty_title(self):
        """Test when title contains only whitespace"""
        data = {"title": " ", "subtitle": "Test Subtitle"}
        form = GalleryForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_gallery_form_no_title(self):
        data = {"subtitle": "Test Subtitle"}
        form = GalleryForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_gallery_form_invalid_slug(self):
        data = {"title": ":", "subtitle": "Test Subtitle"}
        form = GalleryForm(data=data)

        self.assertFalse(form.is_valid())

    def test_valid_gallery_form_title_with_special_characters(self):
        data = {"title": "Title:", "subtitle": "Test Subtitle"}
        form = GalleryForm(data=data)

        self.assertTrue(form.is_valid())


class UserGalleryFormTest(TestCase):
    def setUp(self):
        self.profile = ProfileFactory()

    def test_valid_user_gallery_form(self):
        gallery = GalleryFactory()
        data = {"action": "add", "user": self.profile, "mode": "R"}
        form = UserGalleryForm(gallery=gallery, data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_user_gallery_form_noexist_user(self):
        gallery = GalleryFactory()
        data = {"action": "add", "user": "hello", "mode": "W"}
        form = UserGalleryForm(gallery=gallery, data=data)

        self.assertFalse(form.is_valid())


class ImageFormTest(TestCase):
    def test_valid_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")

        data = {
            "title": "Test Image",
            "legend": "Test Legend",
        }

        files = {"physical": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = ImageForm(data, files)

        self.assertTrue(form.is_valid())
        upload_file.close()

    def test_valid_archive_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "archive-gallery.zip").open("rb")

        data = {}
        files = {"file": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = ArchiveImageForm(data, files)

        self.assertTrue(form.is_valid())
        upload_file.close()

    def test_empty_title_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")

        data = {
            "title": "",
            "legend": "Test Legend",
        }

        files = {"physical": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = ImageForm(data, files)

        self.assertFalse(form.is_valid())
        upload_file.close()

    def test_empty_pic_image_form(self):
        data = {
            "title": "Test Title",
            "legend": "Test Legend",
        }

        files = {"physical": ""}
        form = ImageForm(data, files)

        self.assertFalse(form.is_valid())

    def test_too_big_pic_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "image_test.jpg").open("rb")

        data = {
            "title": "Test Title",
            "legend": "Test Legend",
        }

        files = {"physical": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = ImageForm(data, files)

        self.assertFalse(form.is_valid())
        upload_file.close()

    def test_bot_a_pic_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "forums.yaml").open("rb")

        data = {
            "title": "Test Title",
            "legend": "Test Legend",
        }

        files = {"physical": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = ImageForm(data, files)

        self.assertFalse(form.is_valid())
        upload_file.close()

    def test_too_long_title_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")

        data = {
            "title": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum enim amet.",
            "legend": "Test Legend",
        }

        files = {"physical": SimpleUploadedFile(upload_file.name, upload_file.read())}
        ImageForm(data, files)
        upload_file.close()

    def test_too_long_legend_image_form(self):
        upload_file = (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")

        data = {
            "title": "Test Title",
            "legend": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam condimentum enim amet.",
        }

        files = {"physical": SimpleUploadedFile(upload_file.name, upload_file.read())}
        ImageForm(data, files)
        upload_file.close()


class ImageAsAvatarFormTest(TestCase):
    def test_image_as_avatar_form(self):
        form = ImageAsAvatarForm()

        self.assertFalse(form.is_bound)
