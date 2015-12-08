# coding: utf-8

import os
import shutil

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.gallery.factories import GalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.settings import BASE_DIR
from zds.tutorial.factories import MiniTutorialFactory, ChapterFactory, \
    SubCategoryFactory, LicenceFactory
from zds.tutorial.feeds import LastTutorialsFeedRSS, LastTutorialsFeedATOM
from zds.tutorial.models import Tutorial, Validation


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['tutorial']['repo_path'] = os.path.join(BASE_DIR, 'tutoriels-private-test')
overrided_zds_app['tutorial']['repo_public_path'] = os.path.join(BASE_DIR, 'tutoriels-public-test')
overrided_zds_app['article']['repo_path'] = os.path.join(BASE_DIR, 'article-data-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class LastTutorialsFeedRSSTest(TestCase):

    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.subcat = SubCategoryFactory()

        self.licence = LicenceFactory()
        self.licence.save()

        self.minituto = MiniTutorialFactory()
        self.minituto.authors.add(self.user_author)
        self.minituto.gallery = GalleryFactory()
        self.minituto.licence = self.licence
        self.minituto.save()

        self.chapter = ChapterFactory(
            tutorial=self.minituto,
            position_in_tutorial=1)

        self.staff = StaffProfileFactory().user

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # ask public tutorial
        pub = self.client.post(
            reverse('tutorial-ask-validation'),
            {
                'tutorial': self.minituto.pk,
                'text': u'Ce tuto est excellent',
                'version': self.minituto.sha_draft,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=self.minituto.pk)
        pub = self.client.post(
            reverse('tutorial-reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish tutorial
        pub = self.client.post(
            reverse('tutorial-valid-tutorial'),
            {
                'tutorial': self.minituto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.minituto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(self.minituto.on_line(), True)
        self.assertEquals(len(mail.outbox), 1)

        mail.outbox = []

        self.tutofeed = LastTutorialsFeedRSS()

    def test_is_well_setup(self):
        """ Test that base parameters are Ok """

        self.assertEqual(self.tutofeed.link, '/tutoriels/')
        reftitle = u"Tutoriels sur {}".format(settings.ZDS_APP['site']['litteral_name'])
        self.assertEqual(self.tutofeed.title, reftitle)
        refdescription = u"Les derniers tutoriels parus sur {}.".format(settings.ZDS_APP['site']['litteral_name'])
        self.assertEqual(self.tutofeed.description, refdescription)

        atom = LastTutorialsFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """ basic test sending back the tutorial """

        ret = self.tutofeed.items()
        self.assertEqual(ret[0], self.minituto)

    def test_get_pubdate(self):
        """ test the return value of pubdate """

        ref = Tutorial.objects.get(pk=self.minituto.pk).pubdate
        tuto = self.tutofeed.items()[0]
        ret = self.tutofeed.item_pubdate(item=tuto)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """ test the return value of title """

        ref = self.minituto.title
        tuto = self.tutofeed.items()[0]
        ret = self.tutofeed.item_title(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """ test the return value of description """

        ref = self.minituto.description
        tuto = self.tutofeed.items()[0]
        ret = self.tutofeed.item_description(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """ test the return value of author name """

        ref = self.user_author.username
        tuto = self.tutofeed.items()[0]
        ret = self.tutofeed.item_author_name(item=tuto)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """ test the return value of item link """

        ref = self.minituto.get_absolute_url_online()
        tuto = self.tutofeed.items()[0]
        ret = self.tutofeed.item_link(item=tuto)
        self.assertEqual(ret, ref)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
