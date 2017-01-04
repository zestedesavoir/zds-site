# coding: utf-8

import os
import shutil

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MatchAll

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import BASE_DIR
from django.core.urlresolvers import reverse

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, publish_content
from zds.tutorialv2.models.models_database import PublishedContent, FakeChapter
from zds.forum.factories import TopicFactory, PostFactory, Topic, Post
from zds.forum.tests.tests_views import create_category
from zds.search2.models import ESIndexManager

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
@override_settings(ES_SEARCH_INDEX={'name': 'zds_search_test', 'shards': 5, 'replicas': 1})
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

    def test_basic_search(self):
        """Basic search and filtering"""

        if not self.manager.connected_to_es:
            return

        # 1. Index and test search:
        text = 'test'

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        # create a middle-tutorial and publish it
        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto_draft = tuto.load_version()

        tuto.title = text
        tuto.authors.add(self.user)
        tuto.save()

        tuto_draft.repo_update_top_container(text, tuto.slug, text, text)  # change title to be sure it will match

        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        extract = ExtractFactory(container=chapter1, db_object=tuto)
        extract.repo_update(text, text)

        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published
        tuto.save()

        # nothing was indexed before:
        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 0)

        # index
        for model in self.indexable:
            self.manager.es_bulk_indexing_of_model(model)
        self.manager.refresh_index()

        result = self.client.get(reverse('search:query') + '?q=' + text, follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context['object_list'].execute()

        self.assertEqual(response.hits.total, 4)  # get 4 results

        # 2. Test filtering:
        topic_1 = Topic.objects.get(pk=topic_1.pk)
        post_1 = Post.objects.get(pk=post_1.pk)
        published = PublishedContent.objects.get(pk=published.pk)

        ids = {
            'topic': topic_1.es_id,
            'post': post_1.es_id,
            'publishedcontent': published.es_id,
            'chapter': published.content_public_slug + '__' + chapter1.slug
        }

        for doc_type in [t.get_es_document_type() for t in self.indexable]:

            result = self.client.get(reverse('search:query') + '?q=' + text + '&models=' + doc_type, follow=False)
            self.assertEqual(result.status_code, 200)

            response = result.context['object_list'].execute()

            self.assertEqual(response.hits.total, 1)  # get 1 result of each ...
            self.assertEqual(response[0].meta.doc_type, doc_type)  # ... and only of the good type ...
            self.assertEqual(response[0].meta.id, ids[doc_type])  # .. with the good id !

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
