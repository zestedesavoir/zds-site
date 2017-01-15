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
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, publish_content, \
    PublishedContentFactory
from zds.tutorialv2.models.models_database import PublishedContent, FakeChapter
from zds.forum.factories import TopicFactory, PostFactory, Topic, Post
from zds.forum.tests.tests_views import create_category, Group
from zds.searchv2.models import ESIndexManager

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
@override_settings(ES_SEARCH_INDEX={'name': 'zds_search_test', 'shards': 1, 'replicas': 1})
# 1 shard is not a recommended setting, but since document on different shard may have a different score, it is ok here
class ViewsTests(TestCase):
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

    def test_hidden_post_are_not_result(self):
        """Hidden posts should not come out of the search"""

        if not self.manager.connected_to_es:
            return

        # 1. Index and test search:
        text = 'test'

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.es_bulk_indexing_of_model(Topic)
        self.manager.es_bulk_indexing_of_model(Post)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 2)  # indexation ok

        post_1 = Post.objects.get(pk=post_1.pk)

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)

        response = result.context['object_list'].execute()

        self.assertEqual(response.hits.total, 1)
        self.assertEqual(response[0].meta.id, post_1.es_id)

        # 2. Hide, reindex and search again:
        post_1.hide_comment_by_user(self.staff, u'Un abus de pouvoir comme un autre ;)')
        self.manager.refresh_index()

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 0)  # nothing in the results

    def test_hidden_forums_give_no_results_if_user_not_allowed(self):
        """Long name, isn't ?"""

        if not self.manager.connected_to_es:
            return

        # 1. Create an hidden forum belonging to an hidden group and add staff in it.
        text = 'test'

        group = Group.objects.create(name=u'Les illuminatis anonymes de ZdS')
        _, hidden_forum = create_category(group)

        self.staff.groups.add(group)
        self.staff.save()

        topic_1 = TopicFactory(forum=hidden_forum, author=self.staff, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.es_bulk_indexing_of_model(Topic)
        self.manager.es_bulk_indexing_of_model(Post)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 2)  # indexation ok

        # 2. search without connection and get not result
        result = self.client.get(reverse('search:query') + '?q=' + text, follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 0)

        # 3. Connect with user (not a member of the group), search, and get not result
        self.assertTrue(self.client.login(username=self.user.username, password='hostel77'))

        result = self.client.get(reverse('search:query') + '?q=' + text, follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 0)

        # 4. Connect with staff, search, and get the topic and the post
        self.client.logout()
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))

        result = self.client.get(reverse('search:query') + '?q=' + text, follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)  # ok !

    def test_boosts(self):
        """Will check if boosts are doing their job"""

        if not self.manager.connected_to_es:
            return

        # 1. Create topics (with identical title), posts (with identical text), an article and a tuto
        text = 'test'

        topic_1_solved_sticky = TopicFactory(forum=self.forum, author=self.user)
        topic_1_solved_sticky.title = text
        topic_1_solved_sticky.subtitle = ''
        topic_1_solved_sticky.is_solved = True
        topic_1_solved_sticky.is_sticky = True
        topic_1_solved_sticky.save()

        post_1 = PostFactory(topic=topic_1_solved_sticky, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        post_2_useful = PostFactory(topic=topic_1_solved_sticky, author=self.user, position=2)
        post_2_useful.text = post_2_useful.text_html = text
        post_2_useful.is_useful = True
        post_2_useful.like = 5
        post_2_useful.dislike = 2  # l/d ratio above 1
        post_2_useful.save()

        topic_2_locked = TopicFactory(forum=self.forum, author=self.user, title=text)
        topic_2_locked.title = text
        topic_2_locked.subtitle = ''
        topic_2_locked.is_locked = True
        topic_2_locked.save()

        post_3_ld_below_1 = PostFactory(topic=topic_2_locked, author=self.user, position=1)
        post_3_ld_below_1.text = post_3_ld_below_1.text_html = text
        post_3_ld_below_1.like = 2
        post_3_ld_below_1.dislike = 5  # l/d ratio below 1
        post_3_ld_below_1.save()

        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto_draft = tuto.load_version()

        tuto.title = text
        tuto.authors.add(self.user)
        tuto.save()

        tuto_draft.repo_update_top_container(text, tuto.slug, text, text)

        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        chapter1.repo_update(text, u'Who cares ?', u'Same here')
        ExtractFactory(container=chapter1, db_object=tuto)

        published_tuto = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published_tuto
        tuto.save()

        article = PublishedContentFactory(type='ARTICLE', title=text)
        published_article = PublishedContent.objects.get(content_pk=article.pk)

        for model in self.indexable:
            self.manager.es_bulk_indexing_of_model(model)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 8)

        # 2. Reset all boosts to 1
        for doc_type in settings.ZDS_APP['search']['boosts']:
            for key in settings.ZDS_APP['search']['boosts'][doc_type]:
                settings.ZDS_APP['search']['boosts'][doc_type][key] = 1.0

        # 3. Test posts
        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 3)

        # score are equals without boost:
        self.assertTrue(response[0].meta.score == response[1].meta.score == response[2].meta.score)

        settings.ZDS_APP['search']['boosts']['post']['if_first'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 3)

        self.assertTrue(response[0].meta.score == response[1].meta.score > response[2].meta.score)
        self.assertEquals(response[2].meta.id, str(post_2_useful.pk))  # post 2 is the only one not first

        settings.ZDS_APP['search']['boosts']['post']['if_first'] = 1.0
        settings.ZDS_APP['search']['boosts']['post']['if_useful'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 3)

        self.assertTrue(response[0].meta.score > response[1].meta.score == response[2].meta.score)
        self.assertEquals(response[0].meta.id, str(post_2_useful.pk))  # post 2 is useful

        settings.ZDS_APP['search']['boosts']['post']['if_useful'] = 1.0
        settings.ZDS_APP['search']['boosts']['post']['ld_ratio_above_1'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 3)

        self.assertTrue(response[0].meta.score > response[1].meta.score == response[2].meta.score)
        self.assertEquals(response[0].meta.id, str(post_2_useful.pk))  # post 2 have a l/d ratio of 5/2

        settings.ZDS_APP['search']['boosts']['post']['ld_ratio_above_1'] = 1.0
        settings.ZDS_APP['search']['boosts']['post']['ld_ratio_below_1'] = 2.0  # no one would do that in real life

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 3)

        self.assertTrue(response[0].meta.score > response[1].meta.score == response[2].meta.score)
        self.assertEquals(response[0].meta.id, str(post_3_ld_below_1.pk))  # post 3 have a l/d ratio of 2/5

        settings.ZDS_APP['search']['boosts']['post']['ld_ratio_below_1'] = 1.0

        # 4. Test topics
        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Topic.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)

        # score are equals without boost:
        self.assertTrue(response[0].meta.score == response[1].meta.score)

        settings.ZDS_APP['search']['boosts']['topic']['if_sticky'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Topic.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEqual(response[0].meta.id, str(topic_1_solved_sticky.pk))  # topic 1 is sticky

        settings.ZDS_APP['search']['boosts']['topic']['if_sticky'] = 1.0
        settings.ZDS_APP['search']['boosts']['topic']['if_solved'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Topic.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(topic_1_solved_sticky.pk))  # topic 1 is solved

        settings.ZDS_APP['search']['boosts']['topic']['if_solved'] = 1.0
        settings.ZDS_APP['search']['boosts']['topic']['if_locked'] = 2.0  # no one would do that in real life

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Topic.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(topic_2_locked.pk))  # topic 2 is locked

        settings.ZDS_APP['search']['boosts']['topic']['if_locked'] = 1.0  # no one would do that in real life

        # 5. Test published contents
        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + PublishedContent.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEquals(response.hits.total, 2)

        # score are equals without boost:
        self.assertTrue(response[0].meta.score == response[1].meta.score)

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_article'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + PublishedContent.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(published_article.pk))  # obvious

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_article'] = 1.0
        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_tutorial'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + PublishedContent.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 2)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(published_tuto.pk))  # obvious

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_tutorial'] = 1.0

        # 6. Test global boosts
        # NOTE: score are NOT the same for all documents, no matter how hard it tries to, small differences exists

        for model in self.indexable:

            # set a huge number to overcome the small differences:
            settings.ZDS_APP['search']['boosts'][model.get_es_document_type()]['global'] = 10.0

            result = self.client.get(
                reverse('search:query') + '?q=' + text, follow=False)

            self.assertEqual(result.status_code, 200)
            response = result.context['object_list'].execute()
            self.assertEqual(response.hits.total, 8)

            self.assertEqual(response[0].meta.doc_type, model.get_es_document_type())  # obvious

            settings.ZDS_APP['search']['boosts'][model.get_es_document_type()]['global'] = 1.0

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
