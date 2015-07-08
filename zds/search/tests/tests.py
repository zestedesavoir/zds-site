# coding: utf-8
import shutil
from django.test import override_settings, TestCase
import os
from zds import settings
from zds.gallery.factories import GalleryFactory
from zds.member.factories import ProfileFactory
from zds.search.models import SearchIndexContent, SearchIndexContainer, SearchIndexExtract
from zds.search.utils import reindex_thread, filter_keyword, filter_text
from zds.settings import BASE_DIR
from zds.tutorialv2.factories import LicenceFactory, SubCategoryFactory, PublishableContentFactory, ContainerFactory, \
    ExtractFactory
from zds.tutorialv2.models.models_versioned import VersionedContent

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class TryToIndexTutorialTests(TestCase):
    def setUp(self):
        # Create some tutorials
        self.licence = LicenceFactory()

        self.subcategory = SubCategoryFactory()
        self.subcategory2 = SubCategoryFactory()

        self.user_author_senpai = ProfileFactory().user
        self.user_author = ProfileFactory().user

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author_senpai)
        self.tuto.authors.add(self.user_author)
        self.tuto.gallery = GalleryFactory()
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.subcategory.add(self.subcategory2)
        self.tuto.save()

        self.version_content = VersionedContent(self.tuto.sha_draft,
                                                'Tutorial', self.tuto.title, self.tuto.slug, '')
        self.version_content.is_tutorial = True
        self.part1 = ContainerFactory(parent=self.version_content, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

        self.part2 = ContainerFactory(parent=self.version_content, db_object=self.tuto)
        self.chapter2 = ContainerFactory(parent=self.part2, db_object=self.tuto)

        self.chapter3 = ContainerFactory(parent=self.version_content, db_object=self.tuto)

        # We wanted to test with some article
        self.article = PublishableContentFactory(type='ARTICLE')
        self.article.authors.add(self.user_author_senpai)
        self.article.gallery = GalleryFactory()
        self.article.licence = self.licence
        self.article.subcategory.add(self.subcategory)
        self.article.save()

        self.article_version_content = VersionedContent(self.article.sha_draft,
                                                        'Tutorial', self.article.title, self.article.slug, '')
        self.article_version_content.is_article = True
        self.extract_article1 = ExtractFactory(container=self.article_version_content, db_object=self.article)
        self.extract_article2 = ExtractFactory(container=self.article_version_content, db_object=self.article)

    def test_index_tutorial_article(self):
        '''
        Can at publication time, index a tutorial, this is what we aim for this test.

        We wanted to test, if we can save a tutorial in the search tables. This test cover reindex_thread method in
        search/utils.py file.

        This test doesn't do a verification in the search engine, it just test, if we can save the tutorial in the
        database.
        '''

        # Reindex the tutorial
        reindex_thread(self.version_content, self.tuto)
        reindex_thread(self.article_version_content, self.article)

        self.assertEqual(SearchIndexContent.objects.count(), 2)
        self.assertEqual(SearchIndexContainer.objects.count(), 4)
        self.assertEqual(SearchIndexExtract.objects.count(), 3)

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

                self.assertEqual(content.tags.count(), 2)
                self.assertEqual(content.authors.count(), 2)

                self.assertEqual(SearchIndexContainer.objects.count(), 4)
                self.assertEqual(SearchIndexExtract.objects.count(), 3)

    def test_filter_keyword(self):
        html = "<h1>Keyword h1</h1><h2>Keyword h2</h2><strong>Keyword strong</strong><i>Keyword italic</i>"

        keywords = filter_keyword(html)

        self.assertIn('Keyword h1', keywords)
        self.assertIn('Keyword h2', keywords)
        self.assertIn('Keyword strong', keywords)
        self.assertIn('Keyword italic', keywords)

    def test_filter_text(self):
        html = "<h1>Keyword h1</h1><h2>Keyword h2</h2><strong>Keyword strong</strong><i>Keyword italic</i>"

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
