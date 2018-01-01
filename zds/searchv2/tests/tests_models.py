import os
import shutil

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MatchAll

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from zds.forum.factories import TopicFactory, PostFactory, Topic, Post
from zds.forum.tests.tests_views import create_category
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.searchv2.models import ESIndexManager
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, publish_content
from zds.tutorialv2.models.database import PublishedContent, FakeChapter, PublishableContent
from copy import deepcopy


overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_SEARCH_INDEX={'name': 'zds_search_test', 'shards': 5, 'replicas': 0})
class ESIndexManagerTests(TestCase):
    def setUp(self):
        # don't build PDF to speed up the tests
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.category, self.forum = create_category()

        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.manager = ESIndexManager(**settings.ES_SEARCH_INDEX)
        self.indexable = [FakeChapter, PublishedContent, Topic, Post]

        self.manager.reset_es_index(self.indexable)
        self.manager.setup_custom_analyzer()
        self.manager.refresh_index()

    def test_setup_functions(self):
        """Test the behavior of the reset_es_index(), setup_custom_analyzer() and clear_es_index() functions"""

        if not self.manager.connected_to_es:
            return

        custom_index = {'name': 'some_random_name', 'shards': 3, 'replicas': 1}
        manager = ESIndexManager(**custom_index)

        # in the beginning: the void:
        self.assertTrue(manager.index not in self.manager.es.cat.indices())

        self.assertEqual(manager.index, custom_index['name'])
        self.assertEqual(manager.number_of_shards, custom_index['shards'])
        self.assertEqual(manager.number_of_replicas, custom_index['replicas'])

        # 1. Creation:
        models = [Topic, Post]
        manager.reset_es_index([Topic, Post])
        self.assertTrue(manager.index in manager.es.cat.indices())  # index in !

        index_settings = manager.es.indices.get_settings(index=manager.index)
        self.assertTrue(manager.index in index_settings)
        index_settings = index_settings[manager.index]['settings']['index']

        self.assertEqual(index_settings['provided_name'], manager.index)
        self.assertEqual(index_settings['number_of_shards'], str(manager.number_of_shards))
        self.assertEqual(index_settings['number_of_replicas'], str(manager.number_of_replicas))

        # test mappings
        mappings = manager.es.indices.get_mapping(index=manager.index)
        self.assertTrue(manager.index in mappings)
        mappings = mappings[manager.index]['mappings']

        for model in models:
            self.assertTrue(model.get_es_document_type() in mappings)

        # analyzer
        self.assertTrue('analysis' not in index_settings)
        manager.setup_custom_analyzer()

        index_settings = manager.es.indices.get_settings(index=manager.index)
        self.assertTrue(manager.index in index_settings)
        index_settings = index_settings[manager.index]['settings']['index']
        self.assertTrue('analysis' in index_settings)

        # 3. Clearing
        manager.clear_es_index()
        self.assertTrue(manager.index not in self.manager.es.cat.indices())  # back to the void

    def test_custom_analyzer(self):
        """Test our custom analyzer"""

        if not self.manager.connected_to_es:
            return

        test_sentences = [
            # stemming:
            ('programmation programmer programmateur programmes', ['program', 'program', 'program', 'program']),
            # keep "c" intact:
            ('apprendre à programmer en C', ['aprendr', 'program', 'langage_c']),
            # remove HTML and some special characters:
            ('<p>&laquo; test&#x202F;! &raquo;, en hurlant &hellip;</p>', ['test', 'hurlant']),
            # keep "c++" and "linux" intact:
            ('écrire un programme en C++ avec Linux', ['ecrir', 'program', 'c++', 'linux']),
            # elision:
            ("c'est de l'arnaque", ['arnaqu'])
        ]

        for sentence in test_sentences:
            tokens = self.manager.analyze_sentence(sentence[0])
            self.assertEqual(len(tokens), len(sentence[1]))
            self.assertEqual(tokens, sentence[1])

    def test_indexation(self):
        """test the indexation and deletion of the different documents"""

        if not self.manager.connected_to_es:
            return

        # create a topic with a post
        topic = TopicFactory(forum=self.forum, author=self.user)
        post = PostFactory(topic=topic, author=self.user, position=1)

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
        ExtractFactory(container=chapter1, db_object=tuto)
        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published
        tuto.save()

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertFalse(published.es_already_indexed)
        self.assertTrue(published.es_flagged)

        # 1. index all
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.es_bulk_indexing_of_model(model, force_reindexing=False)
            self.manager.refresh_index()

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
        results = self.manager.setup_search(s).execute()
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

        # 2. Test what reindexation will do:
        new_topic = TopicFactory(forum=self.forum, author=self.user)
        new_post = PostFactory(topic=new_topic, author=self.user, position=1)

        pk_of_topics_to_reindex = []
        for item in Topic.get_es_indexable(force_reindexing=False):
            pk_of_topics_to_reindex.append(item.pk)

        pk_of_posts_to_reindex = []
        for item in Post.get_es_indexable(force_reindexing=False):
            pk_of_posts_to_reindex.append(item.pk)

        self.assertTrue(topic.pk not in pk_of_topics_to_reindex)
        self.assertTrue(new_topic.pk in pk_of_topics_to_reindex)
        self.assertTrue(post.pk not in pk_of_posts_to_reindex)
        self.assertTrue(new_post.pk in pk_of_posts_to_reindex)

        for model in self.indexable:  # ok, so let's index that
            if model is FakeChapter:
                continue
            self.manager.es_bulk_indexing_of_model(model, force_reindexing=False)
        self.manager.refresh_index()

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 6)  # good!

        # 3. Test single deletion:
        new_post = Post.objects.get(pk=new_post.pk)

        self.manager.delete_document(new_post)
        self.manager.refresh_index()

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 5)  # one is missing

        for hit in results:
            self.assertTrue(hit.meta.doc_type != Post.get_es_document_type() or hit.meta.id != new_post.es_id)

        # 4. Test "delete_by_query_deletion":
        topic = Topic.objects.get(pk=topic.pk)
        new_topic = Topic.objects.get(pk=new_topic.pk)

        self.manager.delete_by_query(Topic.get_es_document_type(), MatchAll())  # the two topic are deleted
        self.manager.refresh_index()

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 3)

        for hit in results:
            self.assertTrue(hit.meta.doc_type != Topic.get_es_document_type() or hit.meta.id != new_topic.es_id)
            self.assertTrue(hit.meta.doc_type != Topic.get_es_document_type() or hit.meta.id != topic.es_id)

        # 5. Test that the deletion of an object also triggers its deletion in ES
        post = Post.objects.get(pk=post.pk)
        post.delete()
        self.manager.refresh_index()

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 2)

        for hit in results:
            self.assertTrue(hit.meta.doc_type != Post.get_es_document_type() or hit.meta.id != post.es_id)

        # 6. Test full desindexation:
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.clear_indexing_of_model(model)

        # note "topic" is gone since "post" is gone, due to relationships at the Django level
        new_topic = Topic.objects.get(pk=new_topic.pk)
        new_post = Post.objects.get(pk=new_post.pk)

        self.assertFalse(new_topic.es_already_indexed)
        self.assertTrue(new_topic.es_flagged)
        self.assertFalse(new_post.es_already_indexed)
        self.assertTrue(new_post.es_flagged)

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertFalse(published.es_already_indexed)
        self.assertTrue(published.es_flagged)

    def test_special_case_of_contents(self):
        """test that the old publishedcontent does not stay when a new one is created"""

        if not self.manager.connected_to_es:
            return

        # 1. Create a middle-tutorial, publish it, then index it
        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto.authors.add(self.user)
        tuto.save()

        tuto_draft = tuto.load_version()
        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        ExtractFactory(container=chapter1, db_object=tuto)
        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published
        tuto.save()

        self.manager.es_bulk_indexing_of_model(PublishedContent, force_reindexing=True)  # index
        self.manager.refresh_index()

        first_publication = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertTrue(first_publication.es_already_indexed)
        self.assertFalse(first_publication.es_flagged)

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 2)  # get 2 results, one for the content and one for the chapter

        self.assertEqual(PublishedContent.objects.count(), 1)

        # 2. Change thet title, which will trigger a change in the slug
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version(sha=tuto.sha_draft)

        tuto.title = 'un titre complètement différent!'
        tuto.save()

        versioned.repo_update_top_container(tuto.title, tuto.slug, 'osef', 'osef')
        second_publication = publish_content(tuto, versioned, True)

        tuto.sha_public = versioned.current_version
        tuto.sha_draft = versioned.current_version
        tuto.public_version = second_publication
        tuto.save()

        self.assertEqual(PublishedContent.objects.count(), 2)  # now there is two objects ...
        first_publication = PublishedContent.objects.get(pk=first_publication.pk)
        self.assertTrue(first_publication.must_redirect)  # .. including the first one, for redirection

        self.manager.refresh_index()

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 0)  # the old one is gone (and we need to reindex to get the new one)

        # 3. Check if indexation brings the new one, and not the old one
        self.manager.es_bulk_indexing_of_model(PublishedContent, force_reindexing=True)  # index
        self.manager.refresh_index()

        first_publication = PublishedContent.objects.get(pk=first_publication.pk)
        second_publication = PublishedContent.objects.get(pk=second_publication.pk)

        s = Search()
        s.query(MatchAll())
        results = self.manager.setup_search(s).execute()
        self.assertEqual(len(results), 2)  # Still 2, not 4 !

        found_old = False
        found_new = False

        for hit in results:
            if hit.meta.doc_type == PublishedContent.get_es_document_type():
                if hit.meta.id == first_publication.es_id:
                    found_old = True
                if hit.meta.id == second_publication.es_id:
                    found_new = True

        self.assertTrue(found_new)
        self.assertFalse(found_old)

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
        self.manager.clear_es_index()
