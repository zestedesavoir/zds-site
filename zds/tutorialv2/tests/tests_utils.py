# coding: utf-8

import os
import shutil

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import BASE_DIR

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, LicenceFactory, ExtractFactory
from zds.gallery.factories import GalleryFactory
from zds.tutorialv2.utils import get_target_tagged_tree_for_container, publish_content, unpublish_content, \
    get_target_tagged_tree_for_extract
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent
from django.core.management import call_command

try:
    import ujson as json_reader
except ImportError:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

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
        part2 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto, title="part2")
        part3 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto, title="part3")
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
        tagged_tree = get_target_tagged_tree_for_container(part3, self.tuto_draft)
        self.assertEqual(4, len(tagged_tree))
        paths = {i[0]: i[3] for i in tagged_tree}
        self.assertTrue(part2.get_path(True) in paths)
        self.assertTrue(part3.get_path(True) in paths)
        self.assertTrue(self.chapter1.get_path(True) in paths)
        self.assertTrue(self.part1.get_path(True) in paths)
        self.assertFalse(self.tuto_draft.get_path(True) in paths)
        self.assertTrue(paths[self.chapter1.get_path(True)], "can't be moved to a too deep container")
        self.assertTrue(paths[self.part1.get_path(True)], "can't be moved after or before himself")
        self.assertTrue(paths[part2.get_path(True)], "can be moved after or before part2")
        self.assertFalse(paths[part3.get_path(True)], "can be moved after or before part3")

    def test_publish_content(self):
        """test and ensure the behavior of ``publish_content()`` and ``unpublish_content()``"""

        # 1. Article:
        article = PublishableContentFactory(type='ARTICLE')

        article.authors.add(self.user_author)
        article.gallery = GalleryFactory()
        article.licence = self.licence
        article.save()

        # populate the article
        article_draft = article.load_version()
        ExtractFactory(container=article_draft, db_object=article)
        ExtractFactory(container=article_draft, db_object=article)

        self.assertEqual(len(article_draft.children), 2)

        # publish !
        article = PublishableContent.objects.get(pk=article.pk)
        published = publish_content(article, article_draft)

        self.assertEqual(published.content, article)
        self.assertEqual(published.content_pk, article.pk)
        self.assertEqual(published.content_type, article.type)
        self.assertEqual(published.content_public_slug, article_draft.slug)
        self.assertEqual(published.sha_public, article.sha_draft)

        public = article.load_version(sha=published.sha_public, public=published)
        self.assertIsNotNone(public)
        self.assertTrue(public.PUBLIC)  # its a PublicContent object !
        self.assertEqual(public.type, published.content_type)
        self.assertEqual(public.current_version, published.sha_public)

        # test object created in database
        self.assertEqual(PublishedContent.objects.filter(content=article).count(), 1)
        published = PublishedContent.objects.filter(content=article).last()

        self.assertEqual(published.content_pk, article.pk)
        self.assertEqual(published.content_public_slug, article_draft.slug)
        self.assertEqual(published.content_type, article.type)
        self.assertEqual(published.sha_public, public.current_version)

        # test creation of files:
        self.assertTrue(os.path.isdir(published.get_prod_path()))
        self.assertTrue(os.path.isfile(os.path.join(published.get_prod_path(), 'manifest.json')))
        self.assertTrue(os.path.isfile(public.get_prod_path()))  # normally, an HTML file should exists
        self.assertIsNone(public.introduction)  # since all is in the HTML file, introduction does not exists anymore
        self.assertIsNone(public.conclusion)

        # depublish it !
        unpublish_content(article)
        self.assertEqual(PublishedContent.objects.filter(content=article).count(), 0)  # published object disappear
        self.assertFalse(os.path.exists(public.get_prod_path()))  # article was removed
        # ... For the next tests, I will assume that the unpublication works.

        # 2. Mini-tutorial → Not tested, because at this point, it's the same as an article (with a different metadata)
        # 3. Medium-size tutorial
        midsize_tuto = PublishableContentFactory(type='TUTORIAL')

        midsize_tuto.authors.add(self.user_author)
        midsize_tuto.gallery = GalleryFactory()
        midsize_tuto.licence = self.licence
        midsize_tuto.save()

        # populate with 2 chapters (1 extract each)
        midsize_tuto_draft = midsize_tuto.load_version()
        chapter1 = ContainerFactory(parent=midsize_tuto_draft, db_objet=midsize_tuto)
        ExtractFactory(container=chapter1, db_object=midsize_tuto)
        chapter2 = ContainerFactory(parent=midsize_tuto_draft, db_objet=midsize_tuto)
        ExtractFactory(container=chapter2, db_object=midsize_tuto)

        # publish it
        midsize_tuto = PublishableContent.objects.get(pk=midsize_tuto.pk)
        published = publish_content(midsize_tuto, midsize_tuto_draft)

        self.assertEqual(published.content, midsize_tuto)
        self.assertEqual(published.content_pk, midsize_tuto.pk)
        self.assertEqual(published.content_type, midsize_tuto.type)
        self.assertEqual(published.content_public_slug, midsize_tuto_draft.slug)
        self.assertEqual(published.sha_public, midsize_tuto.sha_draft)

        public = midsize_tuto.load_version(sha=published.sha_public, public=published)
        self.assertIsNotNone(public)
        self.assertTrue(public.PUBLIC)  # its a PublicContent object
        self.assertEqual(public.type, published.content_type)
        self.assertEqual(public.current_version, published.sha_public)

        # test creation of files:
        self.assertTrue(os.path.isdir(published.get_prod_path()))
        self.assertTrue(os.path.isfile(os.path.join(published.get_prod_path(), 'manifest.json')))

        self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), public.introduction)))
        self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), public.conclusion)))

        self.assertEqual(len(public.children), 2)
        for child in public.children:
            self.assertTrue(os.path.isfile(child.get_prod_path()))  # an HTML file for each chapter
            self.assertIsNone(child.introduction)
            self.assertIsNone(child.conclusion)

        # 4. Big tutorial:
        bigtuto = PublishableContentFactory(type='TUTORIAL')

        bigtuto.authors.add(self.user_author)
        bigtuto.gallery = GalleryFactory()
        bigtuto.licence = self.licence
        bigtuto.save()

        # populate with 2 part (1 chapter with 1 extract each)
        bigtuto_draft = bigtuto.load_version()
        part1 = ContainerFactory(parent=bigtuto_draft, db_objet=bigtuto)
        chapter1 = ContainerFactory(parent=part1, db_objet=bigtuto)
        ExtractFactory(container=chapter1, db_object=bigtuto)
        part2 = ContainerFactory(parent=bigtuto_draft, db_objet=bigtuto)
        chapter2 = ContainerFactory(parent=part2, db_objet=bigtuto)
        ExtractFactory(container=chapter2, db_object=bigtuto)

        # publish it
        bigtuto = PublishableContent.objects.get(pk=bigtuto.pk)
        published = publish_content(bigtuto, bigtuto_draft)

        self.assertEqual(published.content, bigtuto)
        self.assertEqual(published.content_pk, bigtuto.pk)
        self.assertEqual(published.content_type, bigtuto.type)
        self.assertEqual(published.content_public_slug, bigtuto_draft.slug)
        self.assertEqual(published.sha_public, bigtuto.sha_draft)

        public = bigtuto.load_version(sha=published.sha_public, public=published)
        self.assertIsNotNone(public)
        self.assertTrue(public.PUBLIC)  # its a PublicContent object
        self.assertEqual(public.type, published.content_type)
        self.assertEqual(public.current_version, published.sha_public)

        # test creation of files:
        self.assertTrue(os.path.isdir(published.get_prod_path()))
        self.assertTrue(os.path.isfile(os.path.join(published.get_prod_path(), 'manifest.json')))

        self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), public.introduction)))
        self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), public.conclusion)))

        self.assertEqual(len(public.children), 2)
        for part in public.children:
            self.assertTrue(os.path.isdir(part.get_prod_path()))  # a directory for each part
            # ... and an HTML file for introduction and conclusion
            self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), part.introduction)))
            self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), part.conclusion)))

            self.assertEqual(len(part.children), 1)

            for chapter in part.children:
                # the HTML file is located in the good directory:
                self.assertEqual(part.get_prod_path(), os.path.dirname(chapter.get_prod_path()))
                self.assertTrue(os.path.isfile(chapter.get_prod_path()))  # an HTML file for each chapter
                self.assertIsNone(chapter.introduction)
                self.assertIsNone(chapter.conclusion)

    def test_tagged_tree_extract(self):
        midsize = PublishableContentFactory(author_list=[self.user_author])
        midsize_draft = midsize.load_version()
        first_container = ContainerFactory(parent=midsize_draft, db_object=midsize)
        second_container = ContainerFactory(parent=midsize_draft, db_object=midsize)
        first_extract = ExtractFactory(container=first_container, db_object=midsize)
        second_extract = ExtractFactory(container=second_container, db_object=midsize)
        tagged_tree = get_target_tagged_tree_for_extract(first_extract, midsize_draft)
        paths = {i[0]: i[3] for i in tagged_tree}
        self.assertTrue(paths[second_extract.get_full_slug()])
        self.assertFalse(paths[second_container.get_path(True)])
        self.assertFalse(paths[first_container.get_path(True)])

    def test_update_manifest(self):
        opts = {}
        shutil.copy(
            os.path.join(BASE_DIR, "fixtures", "tuto", "balise_audio", "manifest.json"),
            os.path.join(BASE_DIR, "fixtures", "tuto", "balise_audio", "manifest2.json")
        )
        LicenceFactory(code="CC BY")
        args = [os.path.join(BASE_DIR, "fixtures", "tuto", "balise_audio", "manifest2.json")]
        call_command('upgrade_manifest_to_v2', *args, **opts)
        manifest = open(os.path.join(BASE_DIR, "fixtures", "tuto", "balise_audio", "manifest2.json"), 'r')
        json = json_reader.loads(manifest.read())

        self.assertTrue(u"version" in json)
        self.assertTrue(u"licence" in json)
        self.assertTrue(u"children" in json)
        self.assertEqual(len(json[u"children"]), 3)
        self.assertEqual(json[u"children"][0][u"object"], u"extract")
        args = [os.path.join(BASE_DIR, "fixtures", "tuto", "big_tuto_v1", "manifest2.json")]
        shutil.copy(
            os.path.join(BASE_DIR, "fixtures", "tuto", "big_tuto_v1", "manifest.json"),
            os.path.join(BASE_DIR, "fixtures", "tuto", "big_tuto_v1", "manifest2.json")
        )
        call_command('upgrade_manifest_to_v2', *args, **opts)
        manifest = open(os.path.join(BASE_DIR, "fixtures", "tuto", "big_tuto_v1", "manifest2.json"), 'r')
        json = json_reader.loads(manifest.read())
        shutil.move(
            os.path.join(BASE_DIR, "fixtures", "tuto", "big_tuto_v1", "manifest2.json"),
            os.path.join(BASE_DIR, "fixtures", "tuto", "big_tuto_v1", "manifest.json")
        )
        self.assertTrue(u"version" in json)
        self.assertTrue(u"licence" in json)
        self.assertTrue(u"children" in json)
        self.assertEqual(len(json[u"children"]), 5)
        self.assertEqual(json[u"children"][0][u"object"], u"container")
        self.assertEqual(len(json[u"children"][0][u"children"]), 3)
        self.assertEqual(len(json[u"children"][0][u"children"][0][u"children"]), 3)
        args = [os.path.join(BASE_DIR, "fixtures", "tuto", "article_v1", "manifest2.json")]
        shutil.copy(
            os.path.join(BASE_DIR, "fixtures", "tuto", "article_v1", "manifest.json"),
            os.path.join(BASE_DIR, "fixtures", "tuto", "article_v1", "manifest2.json")
        )
        call_command('upgrade_manifest_to_v2', *args, **opts)
        manifest = open(os.path.join(BASE_DIR, "fixtures", "tuto", "article_v1", "manifest2.json"), 'r')
        json = json_reader.loads(manifest.read())

        self.assertTrue(u"version" in json)
        self.assertTrue(u"licence" in json)
        self.assertTrue(u"children" in json)
        self.assertEqual(len(json[u"children"]), 1)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
