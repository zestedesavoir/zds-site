# coding: utf-8
from django.contrib.auth.models import Group

import os
import shutil
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from zds.settings import BASE_DIR
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory, \
    SubCategoryFactory, PublishedContentFactory
from zds.gallery.factories import GalleryFactory
from zds.forum.factories import ForumFactory, CategoryFactory

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ContentTests(TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        self.tuto.gallery = GalleryFactory()
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        self.beta_forum = ForumFactory(
            pk=settings.ZDS_APP['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)  # ensure that the forum, for the beta versions, is created

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()
        self.external = UserFactory(
            username=settings.ZDS_APP["member"]["external_account"],
            password="anything")

    def test_public_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishedContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type="ARTICLE")
        self.client.logout()
        resp = self.client.get(reverse("tutorial:list"))
        self.assertContains(resp, tutorial.title, count=1)
        self.assertNotContains(resp, tutorial_unpublished.title)
        resp = self.client.get(reverse("article:list"))
        self.assertContains(resp, article.title, count=1)
        self.assertNotContains(resp, article_unpublished.title)
        resp = self.client.get(reverse("content:find-tutorial", args=[self.user_author.pk]) + "?filter=public")
        self.assertContains(resp, tutorial.title, count=1)
        self.assertNotContains(resp, tutorial_unpublished.title)
        resp = self.client.get(reverse("content:find-tutorial", args=[self.user_author.pk]) + "?filter=redaction")
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get(reverse("content:find-article", args=[self.user_author.pk]) + "?filter=public")
        self.assertContains(resp, article.title, count=1)
        self.assertNotContains(resp, article_unpublished.title)
        resp = self.client.get(reverse("content:find-article", args=[self.user_author.pk]) + "?filter=redaction")
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get(reverse("content:find-article", args=[self.user_author.pk]) + "?filter=chuck-norris")
        self.assertEqual(resp.status_code, 404)

    def test_private_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishedContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type="ARTICLE")
        self.client.login(
            username=self.user_author.username,
            password='hostel77')
        resp = self.client.get(reverse("content:find-tutorial", args=[self.user_author.pk]))
        self.assertContains(resp, tutorial.title, count=1)
        self.assertContains(resp, tutorial_unpublished.title, count=1)
        self.assertContains(resp, "content-illu", count=2)
        resp = self.client.get(reverse("content:find-article", args=[self.user_author.pk]))
        self.assertContains(resp, article.title, count=1)
        self.assertContains(resp, article_unpublished.title)
        self.assertContains(resp, "content-illu", count=2)

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
