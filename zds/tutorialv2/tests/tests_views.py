# coding: utf-8

import os
import shutil

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from zds.settings import SITE_ROOT
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory
from zds.tutorialv2.models import PublishableContent
from zds.gallery.factories import GalleryFactory

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

    def test_ensure_access(self):
        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for user
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        self.client.logout()

        # check access for public (get 302, login)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login with staff
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for staff (get 200)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

    def test_deletion(self):
        """Ensure deletion behavior"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # create a new tutorial
        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto.authors.add(self.user_author)
        tuto.gallery = GalleryFactory()
        tuto.licence = self.licence
        tuto.save()

        versioned = tuto.load_version()
        path = versioned.get_path()

        # delete it
        result = self.client.get(
            reverse('content:delete', args=[tuto.pk, tuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 405)  # get method is not allowed for deleting

        result = self.client.post(
            reverse('content:delete', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertFalse(os.path.isfile(path))  # deletion get right ;)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
