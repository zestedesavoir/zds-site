# coding: utf-8
from django.contrib.auth.models import Group

import os
import shutil
import datetime
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from zds.settings import BASE_DIR
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory, \
    SubCategoryFactory, PublishedContentFactory, ValidationFactory
from zds.gallery.factories import UserGalleryFactory
from zds.forum.factories import ForumFactory, CategoryFactory

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
@override_settings(ES_ENABLED=False)
class ContentTests(TestCase):
    def setUp(self):

        # don't build PDF to speed up the tests
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

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
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode='W')
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
        bot = Group(name=settings.ZDS_APP['member']['bot_group'])
        bot.save()
        self.external = UserFactory(
            username=settings.ZDS_APP['member']['external_account'],
            password='anything')

    def test_public_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishableContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type='ARTICLE')
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type='ARTICLE')
        self.client.logout()
        resp = self.client.get(reverse('tutorial:list'))
        self.assertContains(resp, tutorial.title)
        self.assertNotContains(resp, tutorial_unpublished.title)
        resp = self.client.get(reverse('article:list'))
        self.assertContains(resp, article.title)
        self.assertNotContains(resp, article_unpublished.title)
        resp = self.client.get(reverse('content:find-tutorial', args=[self.user_author.pk]) + '?filter=public')
        self.assertContains(resp, tutorial.title)
        self.assertNotContains(resp, tutorial_unpublished.title)
        resp = self.client.get(reverse('content:find-tutorial', args=[self.user_author.pk]) + '?filter=redaction')
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]) + '?filter=public')
        self.assertContains(resp, article.title)
        self.assertNotContains(resp, article_unpublished.title)
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]) + '?filter=redaction')
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]) + '?filter=chuck-norris')
        self.assertEqual(resp.status_code, 404)

    def test_private_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishableContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type='ARTICLE')
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type='ARTICLE')
        self.client.login(
            username=self.user_author.username,
            password='hostel77')
        resp = self.client.get(reverse('content:find-tutorial', args=[self.user_author.pk]))
        self.assertContains(resp, tutorial.title)
        self.assertContains(resp, tutorial_unpublished.title)
        self.assertContains(resp, 'content-illu')
        resp = self.client.get(reverse('content:find-article', args=[self.user_author.pk]))
        self.assertContains(resp, article.title)
        self.assertContains(resp, article_unpublished.title)
        self.assertContains(resp, 'content-illu')

    def test_validation_list(self):
        """ensure the behavior of the `validation:list` page (with filters)"""

        text = u'Ceci est un éléphant'

        tuto_not_reserved = PublishableContentFactory(type='TUTORIAL', author_list=[self.user_author])
        tuto_reserved = PublishableContentFactory(type='TUTORIAL', author_list=[self.user_author])
        article_not_reserved = PublishableContentFactory(type='ARTICLE', author_list=[self.user_author])
        article_reserved = PublishableContentFactory(type='ARTICLE', author_list=[self.user_author])

        all_contents = [tuto_not_reserved, tuto_reserved, article_not_reserved, article_reserved]
        reserved_contents = [tuto_reserved, article_reserved]

        # apply a filter to test category filter
        subcat = SubCategoryFactory()
        article_reserved.subcategory.add(subcat)
        article_reserved.save()

        # send in validation
        for content in all_contents:
            v = ValidationFactory(content=content, status='PENDING')
            v.date_proposition = datetime.datetime.now()
            v.version = content.sha_draft
            v.comment_authors = text

            if content in reserved_contents:
                v.validator = self.user_staff
                v.date_reserve = datetime.datetime.now()
                v.status = 'PENDING_V'

            v.save()

        # first, test access for public
        result = self.client.get(reverse('validation:list'), follow=False)
        self.assertEqual(result.status_code, 302)  # get 302 → redirection to login

        # connect with author:
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.get(reverse('validation:list'), follow=False)
        self.assertEqual(result.status_code, 403)  # get 403 not allowed

        self.client.logout()

        # connect with staff:
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        response = self.client.get(reverse('validation:list'), follow=False)
        self.assertEqual(response.status_code, 200)  # OK

        validations = response.context['validations']
        self.assertEqual(len(validations), 4)  # a total of 4 contents in validation

        # test filters
        response = self.client.get(reverse('validation:list') + '?type=article', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 articles

        response = self.client.get(reverse('validation:list') + '?type=tuto', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 articles

        response = self.client.get(reverse('validation:list') + '?type=orphan', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 not-reserved content

        for validation in validations:
            self.assertFalse(validation.content in reserved_contents)

        response = self.client.get(reverse('validation:list') + '?type=reserved', follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 2)  # 2 reserved content

        for validation in validations:
            self.assertTrue(validation.content in reserved_contents)

        response = self.client.get(reverse('validation:list') + '?subcategory={}'.format(subcat.pk), follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context['validations']
        self.assertEqual(len(validations), 1)  # 1 content with this category

        self.assertEqual(validations[0].content, article_reserved)  # the right content

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        # re-activate PDF build
        settings.ZDS_APP['content']['build_pdf_when_published'] = True
