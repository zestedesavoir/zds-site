# coding: utf-8
import shutil
from django.test import override_settings, TestCase
from django.contrib.auth.models import Group
import os
from zds import settings
from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import StaffProfileFactory, UserFactory
from zds.forum.factories import ForumFactory, CategoryFactory
from zds.member.factories import ProfileFactory
from zds.search.models import SearchIndexContent, SearchIndexContainer, SearchIndexExtract
from zds.search.utils import filter_keyword, filter_text, reindex_content
from zds.settings import BASE_DIR
from zds.tutorialv2.factories import LicenceFactory, SubCategoryFactory, PublishableContentFactory, ContainerFactory, \
    ExtractFactory
from zds.tutorialv2.publication_utils import publish_content

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class TryToIndexTutorialTests(TestCase):
    def setUp(self):

        # don't build PDF to speed up the tests
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        bot = Group(name=settings.ZDS_APP['member']['bot_group'])
        bot.save()
        self.external = UserFactory(
            username=settings.ZDS_APP['member']['external_account'],
            password='anything')

        self.beta_forum = ForumFactory(
            pk=settings.ZDS_APP['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)  # ensure that the forum, for the beta versions, is created

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        # create a tutorial
        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode='W')
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        # fill it with one part, containing one chapter, containing one extract
        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

        # then, publish it !
        version = self.tuto_draft.current_version
        self.published_tuto = publish_content(self.tuto, self.tuto_draft, is_major_update=True)

        self.tuto.sha_public = version
        self.tuto.sha_draft = version
        self.tuto.public_version = self.published_tuto
        self.tuto.save()

        # create an article
        self.article = PublishableContentFactory(type='ARTICLE')
        self.article.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.article.gallery, user=self.user_author, mode='W')
        self.article.licence = self.licence
        self.article.subcategory.add(self.subcategory)
        self.article.save()

        # fill it with one extract
        self.article_draft = self.article.load_version()
        self.extract1 = ExtractFactory(container=self.article_draft, db_object=self.article)

        # then, publish it !
        version = self.article_draft.current_version
        self.published_article = publish_content(self.article, self.article_draft, is_major_update=True)

        self.article.sha_public = version
        self.article.sha_draft = version
        self.article.public_version = self.published_article
        self.article.save()

    def test_index_tutorial_article(self):
        """
        Can at publication time, index a tutorial, this is what we aim for this test.

        We wanted to test, if we can save a tutorial in the search tables. This test cover reindex_thread method in
        search/utils.py file.

        This test doesn't do a verification in the search engine, it just test, if we can save the tutorial in the
        database.
        """

        # Reindex the tutorial
        reindex_content(self.published_tuto)
        reindex_content(self.published_article)

        self.assertEqual(SearchIndexContent.objects.count(), 2)
        self.assertEqual(SearchIndexContainer.objects.count(), 2)
        self.assertEqual(SearchIndexExtract.objects.count(), 2)

        for content in SearchIndexContent.objects.all():
            if content.type == 'article':
                self.assertIsNotNone(content.publishable_content)
                self.assertEqual(content.title, self.article.title)
                self.assertEqual(content.description, self.article.description)

                self.assertEqual(content.licence, self.licence.title)
                if self.article.image:
                    self.assertEqual(content.url_image, self.article.image.get_absolute_url())

                self.assertEqual(content.tags.count(), 1)
                self.assertEqual(content.authors.count(), 1)
            else:
                self.assertIsNotNone(content.publishable_content)
                self.assertEqual(content.title, self.tuto.title)
                self.assertEqual(content.description, self.tuto.description)

                self.assertEqual(content.licence, self.licence.title)
                if self.tuto.image:
                    self.assertEqual(content.url_image, self.tuto.image.get_absolute_url())

                self.assertEqual(content.tags.count(), 1)
                self.assertEqual(content.authors.count(), 1)

    def test_filter_keyword(self):
        html = '<h1>Keyword h1</h1><h2>Keyword h2</h2><strong>Keyword strong</strong><em>Keyword italic</em>'

        keywords = filter_keyword(html)

        self.assertIn('Keyword h1', keywords)
        self.assertIn('Keyword h2', keywords)
        self.assertIn('Keyword strong', keywords)
        self.assertIn('Keyword italic', keywords)

    def test_filter_text(self):
        html = '<h1>Keyword h1</h1><h2>Keyword h2</h2><strong>Keyword strong</strong><em>Keyword italic</em>'

        words = filter_text(html)

        self.assertIn('Keyword h1', words)
        self.assertIn('Keyword h2', words)
        self.assertIn('Keyword strong', words)
        self.assertIn('Keyword italic', words)

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
