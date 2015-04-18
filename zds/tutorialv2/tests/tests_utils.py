# coding: utf-8

import os

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import BASE_DIR

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, LicenceFactory
from zds.gallery.factories import GalleryFactory
from zds.tutorialv2.utils import get_target_tagged_tree_for_container
# from zds.tutorialv2.models import Container, Extract, VersionedContent

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class UtilsTests(TestCase):

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

    def test_get_target_tagged_tree_for_container(self):
        part2 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        part3 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        tagged_tree = get_target_tagged_tree_for_container(self.part1, self.tuto_draft)

        self.assertEqual(4, len(tagged_tree))
        paths = {i[0]: i[3] for i in tagged_tree}
        self.assertTrue(part2.get_path(True) in paths)
        self.assertTrue(part3.get_path(True) in paths)
        self.assertTrue(self.chapter1.get_path(True) in paths)
        self.assertTrue(self.part1.get_path(True) in paths)
        self.assertFalse(self.tuto_draft.get_path(True) in paths)
        self.assertFalse(paths[self.chapter1.get_path(True)], "can't be moved to a too deep container")
        self.assertFalse(paths[self.part1.get_path(True)], "can't be moved after or before himself")
        self.assertTrue(paths[part2.get_path(True)], "can be moved after or before part2")
        self.assertTrue(paths[part3.get_path(True)], "can be moved after or before part3")
