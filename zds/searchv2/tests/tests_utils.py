import os
import shutil

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MatchAll

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory
from zds.tutorialv2.models.database import PublishedContent
from zds.tutorialv2.publication_utils import publish_content
from zds.forum.factories import TopicFactory, PostFactory, Topic, Post
from zds.forum.tests.tests_views import create_category
from zds.searchv2.models import ESIndexManager
from copy import deepcopy

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_SEARCH_INDEX={'name': 'zds_search_test', 'shards': 5, 'replicas': 0})
class UtilsTests(TestCase):
    def setUp(self):
        # don't build PDF to speed up the tests
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.category, self.forum = create_category()

        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def test_es_manager(self):
        """Test the behavior of the ``es_manager`` command"""

        if not self.index_manager.connected_to_es:
            return

        # in the beginning: the void
        self.assertTrue(self.index_manager.index not in self.index_manager.es.cat.indices())

        text = 'Ceci est un texte de test'

        # create a topic with a post
        topic = TopicFactory(forum=self.forum, author=self.user, title=text)
        post = PostFactory(topic=topic, author=self.user, position=1)
        post.text = post.text_html = text
        post.save()

        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(pk=post.pk)

        self.assertFalse(topic.es_already_indexed)
        self.assertTrue(topic.es_flagged)
        self.assertFalse(post.es_already_indexed)
        self.assertTrue(post.es_flagged)

        # create a middle-tutorial and publish it
        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto.authors.add(self.user)
        tuto.save()

        tuto_draft = tuto.load_version()
        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        chapter1.repo_update(text, text, text)
        extract1 = ExtractFactory(container=chapter1, db_object=tuto)
        version = extract1.repo_update(text, text)
        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = version
        tuto.sha_draft = version
        tuto.public_version = published
        tuto.save()

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertFalse(published.es_already_indexed)
        self.assertTrue(published.es_flagged)

        # 1. test "index-all"
        call_command('es_manager', 'index_all')
        self.assertTrue(self.index_manager.es.indices.exists(self.index_manager.index))
        self.index_manager.index_exists = True

        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(pk=post.pk)

        self.assertTrue(topic.es_already_indexed)
        self.assertFalse(topic.es_flagged)
        self.assertTrue(post.es_already_indexed)
        self.assertFalse(post.es_flagged)

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertTrue(published.es_already_indexed)
        self.assertFalse(published.es_flagged)

        s = Search()
        s.query(MatchAll())
        results = self.index_manager.setup_search(s).execute()
        self.assertEqual(len(results), 4)  # get 4 results, one of each type

        must_contain = {'post': False, 'topic': False, 'publishedcontent': False, 'chapter': False}
        id_must_be = {
            'post': str(post.pk),
            'topic': str(topic.pk),
            'publishedcontent': str(published.pk),
            'chapter': tuto.slug + '__' + chapter1.slug
        }

        for hit in results:
            doc_type = hit.meta.doc_type
            must_contain[doc_type] = True
            self.assertEqual(hit.meta.id, id_must_be[doc_type])

        self.assertTrue(all(must_contain))

        # 2. test "clear"
        self.assertTrue(self.index_manager.index in self.index_manager.es.cat.indices())  # index in

        call_command('es_manager', 'clear')
        self.assertFalse(self.index_manager.es.indices.exists(self.index_manager.index))
        self.index_manager.index_exists = False

        # must reset every object
        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(pk=post.pk)

        self.assertFalse(topic.es_already_indexed)
        self.assertTrue(topic.es_flagged)
        self.assertFalse(post.es_already_indexed)
        self.assertTrue(post.es_flagged)

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertFalse(published.es_already_indexed)
        self.assertTrue(published.es_flagged)

        self.assertTrue(self.index_manager.index not in self.index_manager.es.cat.indices())  # index wiped out !

        # 3. test "setup"
        call_command('es_manager', 'setup')
        self.assertTrue(self.index_manager.es.indices.exists(self.index_manager.index))
        self.index_manager.index_exists = True

        self.assertTrue(self.index_manager.index in self.index_manager.es.cat.indices())  # index back in ...

        s = Search()
        s.query(MatchAll())
        results = self.index_manager.setup_search(s).execute()
        self.assertEqual(len(results), 0)  # ... but with nothing in it

        result = self.index_manager.es.indices.get_settings(index=self.index_manager.index)
        settings_index = result[self.index_manager.index]['settings']['index']
        self.assertTrue('analysis' in settings_index)  # custom analyzer was setup

        # 4. test "index-flagged" once ...
        call_command('es_manager', 'index_flagged')

        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(pk=post.pk)

        self.assertTrue(topic.es_already_indexed)
        self.assertFalse(topic.es_flagged)
        self.assertTrue(post.es_already_indexed)
        self.assertFalse(post.es_flagged)

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertTrue(published.es_already_indexed)
        self.assertFalse(published.es_flagged)

        s = Search()
        s.query(MatchAll())
        results = self.index_manager.setup_search(s).execute()
        self.assertEqual(len(results), 4)  # get the 4 results back

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        # re-active PDF build
        settings.ZDS_APP['content']['build_pdf_when_published'] = True

        # delete index:
        self.index_manager.clear_es_index()
