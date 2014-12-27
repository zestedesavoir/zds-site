# coding: utf-8

# NOTE : this file is only there for tests purpose, it will be deleted in final version

import os
import shutil

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import SITE_ROOT

from zds.member.factories import ProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory
from zds.gallery.factories import GalleryFactory

# from zds.tutorialv2.models import Container, Extract, VersionedContent


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
class ContentTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()

        self.user_author = ProfileFactory().user
        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        self.tuto.gallery = GalleryFactory()
        self.tuto.licence = self.licence
        self.tuto.save()

        self.tuto_draft = self.tuto.load_version()
        self.chapter1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter2 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

    def test_workflow_content(self):
        versioned = self.tuto.load_version()
        self.assertEqual(self.tuto_draft.title, versioned.title)
        self.assertEqual(self.chapter1.title, versioned.children[0].title)
        self.assertEqual(self.extract1.title, versioned.children[0].children[0].title)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
