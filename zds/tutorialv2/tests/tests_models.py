# coding: utf-8

import os
import shutil

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import BASE_DIR

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory
from zds.gallery.factories import GalleryFactory

# from zds.tutorialv2.models import Container, Extract, VersionedContent

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
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

    def test_workflow_repository(self):
        """
        Test to ensure the behavior of repo_*() functions :
        - if they change the filesystem as they are suppose to ;
        - if they change the `self.sha_*` as they are suppose to.
        """

        new_title = u'Un nouveau titre'
        other_new_title = u'Un titre différent'
        random_text = u'J\'ai faim!'
        other_random_text = u'Oh, du chocolat <3'

        versioned = self.tuto.load_version()
        current_version = versioned.current_version
        slug_repository = versioned.slug_repository

        # VersionedContent:
        old_path = versioned.get_path()
        self.assertTrue(os.path.isdir(old_path))
        new_slug = versioned.get_unique_slug(new_title)  # normally, you get a new slug by asking database !

        versioned.repo_update_top_container(new_title, new_slug, random_text, random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        new_path = versioned.get_path()
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isdir(new_path))
        self.assertFalse(os.path.isdir(old_path))

        self.assertNotEqual(slug_repository, versioned.slug_repository)  # if this test fail, you're in trouble

        # Container:

        # 1. add new part:
        versioned.repo_add_container(new_title, random_text, random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        part = versioned.children[-1]
        old_path = part.get_path()
        self.assertTrue(os.path.isdir(old_path))
        self.assertTrue(os.path.exists(os.path.join(versioned.get_path(), part.introduction)))
        self.assertTrue(os.path.exists(os.path.join(versioned.get_path(), part.conclusion)))
        self.assertEqual(part.get_introduction(), random_text)
        self.assertEqual(part.get_conclusion(), random_text)

        # 2. update the part
        part.repo_update(other_new_title, other_random_text, other_random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        new_path = part.get_path()
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isdir(new_path))
        self.assertFalse(os.path.isdir(old_path))

        self.assertEqual(part.get_introduction(), other_random_text)
        self.assertEqual(part.get_conclusion(), other_random_text)

        # 3. delete it
        part.repo_delete()  # boom !
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        self.assertFalse(os.path.isdir(new_path))

        # Extract :

        # 1. add new extract
        versioned.repo_add_container(new_title, random_text, random_text)  # need to add a new part before
        part = versioned.children[-1]

        part.repo_add_extract(new_title, random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        extract = part.children[-1]
        old_path = extract.get_path()
        self.assertTrue(os.path.isfile(old_path))
        self.assertEqual(extract.get_text(), random_text)

        # 2. update extract
        extract.repo_update(other_new_title, other_random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        new_path = extract.get_path()
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isfile(new_path))
        self.assertFalse(os.path.isfile(old_path))

        self.assertEqual(extract.get_text(), other_random_text)

        # 3. update parent and see if it still works:
        part.repo_update(other_new_title, other_random_text, other_random_text)

        old_path = new_path
        new_path = extract.get_path()

        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isfile(new_path))
        self.assertFalse(os.path.isfile(old_path))

        self.assertEqual(extract.get_text(), other_random_text)

        # 4. Boom, no more extract
        extract.repo_delete()
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)

        self.assertFalse(os.path.exists(new_path))

    def test_if_none(self):
        """Test the case where introduction and conclusion are `None`"""

        given_title = u'La vie secrète de Clem\''
        some_text = u'Tous ces secrets (ou pas)'
        versioned = self.tuto.load_version()
        versioned.repo_add_container(given_title, None, None)  # add a new part with `None` for intro and conclusion

        new_part = versioned.children[-1]
        self.assertIsNone(new_part.introduction)
        self.assertIsNone(new_part.conclusion)

        new_part.repo_update(given_title, None, None)  # still `None`
        self.assertIsNone(new_part.introduction)
        self.assertIsNone(new_part.conclusion)

        new_part.repo_update(given_title, some_text, some_text)
        self.assertIsNotNone(new_part.introduction)  # now, value given
        self.assertIsNotNone(new_part.conclusion)

        old_intro = new_part.introduction
        old_conclu = new_part.conclusion
        self.assertTrue(os.path.isfile(os.path.join(versioned.get_path(), old_intro)))
        self.assertTrue(os.path.isfile(os.path.join(versioned.get_path(), old_conclu)))

        new_part.repo_update(given_title, None, None)  # and we go back to `None`
        self.assertIsNone(new_part.introduction)
        self.assertIsNone(new_part.conclusion)
        self.assertFalse(os.path.isfile(os.path.join(versioned.get_path(), old_intro)))  # introduction is deleted
        self.assertFalse(os.path.isfile(os.path.join(versioned.get_path(), old_conclu)))

        new_part.repo_update(given_title, '', '')  # empty string != `None`
        self.assertIsNotNone(new_part.introduction)
        self.assertIsNotNone(new_part.conclusion)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
