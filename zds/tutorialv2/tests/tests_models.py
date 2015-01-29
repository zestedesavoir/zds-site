# coding: utf-8

import os
import shutil

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import SITE_ROOT

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory
from zds.gallery.factories import GalleryFactory

# from zds.tutorialv2.models import Container, Extract, VersionedContent

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(SITE_ROOT, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(SITE_ROOT, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ContentTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()

        self.user_author = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        self.tuto.gallery = GalleryFactory()
        self.tuto.licence = self.licence
        self.tuto.save()

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

    def test_workflow_content(self):
        """
        General tests for a content
        """
        # ensure the usability of manifest
        versioned = self.tuto.load_version()
        self.assertEqual(self.tuto_draft.title, versioned.title)
        self.assertEqual(self.part1.title, versioned.children[0].title)
        self.assertEqual(self.extract1.title, versioned.children[0].children[0].children[0].title)

        # ensure url resolution project using dictionary :
        self.assertTrue(self.part1.slug in versioned.children_dict.keys())
        self.assertTrue(self.chapter1.slug in versioned.children_dict[self.part1.slug].children_dict)

    def test_ensure_unique_slug(self):
        """
        Ensure that slugs for a container or extract are always unique
        """
        # get draft version
        versioned = self.tuto.load_version()

        # forbidden slugs :
        slug_to_test = ['introduction', 'conclusion']

        for slug in slug_to_test:
            new_slug = versioned.get_unique_slug(slug)
            self.assertNotEqual(slug, new_slug)
            self.assertTrue(new_slug in versioned.slug_pool)  # ensure new slugs are in slug pool

        # then test with "real" containers and extracts :
        new_chapter_1 = ContainerFactory(title='aa', parent=versioned, db_object=self.tuto)
        new_chapter_2 = ContainerFactory(title='aa', parent=versioned, db_object=self.tuto)
        self.assertNotEqual(new_chapter_1.slug, new_chapter_2.slug)

        new_extract_1 = ExtractFactory(title='aa', container=new_chapter_1, db_object=self.tuto)
        self.assertEqual(new_extract_1.slug, new_chapter_1.slug)  # different level can have the same slug !

        new_extract_2 = ExtractFactory(title='aa', container=new_chapter_2, db_object=self.tuto)
        self.assertEqual(new_extract_2.slug, new_extract_1.slug)  # not the same parent, so allowed

        new_extract_3 = ExtractFactory(title='aa', container=new_chapter_1, db_object=self.tuto)
        self.assertNotEqual(new_extract_3.slug, new_extract_1.slug)  # same parent, forbidden

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
