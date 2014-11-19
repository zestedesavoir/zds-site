# coding: utf-8
from django.test import TestCase

from zds.tutorial.factories import SubCategoryFactory, LicenceFactory
from zds.tutorial.forms import TutorialForm
from zds import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django.test.utils import override_settings
from zds.settings import SITE_ROOT


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
class TutorialFormTest(TestCase):
    """ Check the form to tutorial """
    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'

        self.subcat = SubCategoryFactory()

        self.licence = LicenceFactory()
        self.licence.save()

    def test_valid_big_tutorial_form(self):
        upload_file = open(os.path.join(settings.SITE_ROOT, 'fixtures', 'logo.png'), 'r')
        files = {
            'image': SimpleUploadedFile(upload_file.name, upload_file.read())
        }
        data = {
            'title': 'Tutoriel Big',
            'description': 'Description du tutoriel',
            'introduction': u"O rage",
            'conclusion': u"O desespoir",
            "subcategory": [self.subcat.pk],
            'type': u"BIG",
            'licence': self.licence.pk,
            'msg_commit': u"Init"
        }
        form = TutorialForm(data, files)
        self.assertTrue(form.is_valid())
        upload_file.close()

    def test_valid_mini_tutorial_form(self):
        upload_file = open(os.path.join(settings.SITE_ROOT, 'fixtures', 'logo.png'), 'r')
        files = {
            'image': SimpleUploadedFile(upload_file.name, upload_file.read())
        }
        data = {
            'title': 'Tutoriel Big',
            'description': 'Description du tutoriel',
            'introduction': u"O rage",
            'conclusion': u"O desespoir",
            "subcategory": [self.subcat.pk],
            'type': u"MINI",
            'licence': self.licence.pk,
            'msg_commit': u"Init"
        }
        form = TutorialForm(data, files)
        self.assertTrue(form.is_valid())
        upload_file.close()
