# coding: utf-8

import os
import json
import shutil
import datetime

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MatchAll

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import BASE_DIR
from django.core.urlresolvers import reverse

from zds.forum.factories import TopicFactory, PostFactory, Topic, Post, TagFactory
from zds.forum.tests.tests_views import create_category, Group
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.searchv2.models import ESIndexManager
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, publish_content, \
    PublishedContentFactory, SubCategoryFactory
from zds.tutorialv2.models.models_database import PublishedContent, FakeChapter, PublishableContent

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
# 1 shard is not a recommended setting, but since document on different shard may have a different score, it is ok here
@override_settings(ES_SEARCH_INDEX={'name': 'zds_search_test', 'shards': 1, 'replicas': 0})
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
            if model is FakeChapter:
                continue
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
            'topic': [topic_1.es_id],
            'post': [post_1.es_id],
            'content': [published.es_id, published.content_public_slug + '__' + chapter1.slug],
        }

        search_groups = [k for k, v in settings.ZDS_APP['search']['search_groups'].iteritems()]
        group_to_model = {k: v[1] for k, v in settings.ZDS_APP['search']['search_groups'].iteritems()}

        for doc_type in search_groups:
            result = self.client.get(reverse('search:query') + '?q=' + text + '&models=' + doc_type, follow=False)
            self.assertEqual(result.status_code, 200)

            response = result.context['object_list'].execute()

            self.assertEqual(response.hits.total, len(ids[doc_type]))  # get 1 result of each ...
            for i, r in enumerate(response):
                self.assertIn(r.meta.doc_type, group_to_model[doc_type])  # ... and only of the right type ...
                self.assertEqual(r.meta.id, ids[doc_type][i])  # .. with the right id !

    def test_get_similar_topics(self):
        """Get similar topics lists"""

        if not self.manager.connected_to_es:
            return

        text = 'Clem ne se mange pas'

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        text = 'Clem est la meilleure mascotte'

        topic_2 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_2 = PostFactory(topic=topic_2, author=self.user, position=1)
        post_2.text = post_1.text_html = text
        post_2.save()

        # 1. Should not get any result
        result = self.client.get(reverse('search:similar') + '?q=est', follow=False)
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.content)
        self.assertEqual(len(content['results']), 0)

        # index
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.es_bulk_indexing_of_model(model)
        self.manager.refresh_index()

        # 2. Should not get two results
        result = self.client.get(reverse('search:similar') + '?q=mange', follow=False)
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.content)
        self.assertEqual(len(content['results']), 1)

        # 2. Should not get two results
        result = self.client.get(reverse('search:similar') + '?q=Clem', follow=False)
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.content)
        self.assertEqual(len(content['results']), 2)

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

        # 1. Create an hidden forum belonging to a hidden staff group.
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
        """Check if boosts are doing their job"""

        if not self.manager.connected_to_es:
            return

        # 1. Create topics (with identical titles), posts (with identical texts), an article and a tuto
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

        opinion_not_picked = PublishedContentFactory(type='OPINION', title=text)
        published_opinion_not_picked = PublishedContent.objects.get(content_pk=opinion_not_picked.pk)

        opinion_picked = PublishedContentFactory(type='OPINION', title=text)
        opinion_picked.sha_picked = opinion_picked.sha_draft
        opinion_picked.date_picked = datetime.datetime.now()
        opinion_picked.save()

        published_opinion_picked = PublishedContent.objects.get(content_pk=opinion_picked.pk)

        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.es_bulk_indexing_of_model(model)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 10)

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
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEquals(response.hits.total, 5)

        # score are equals without boost:
        self.assertTrue(response[0].meta.score ==
                        response[1].meta.score ==
                        response[2].meta.score ==
                        response[3].meta.score ==
                        response[4].meta.score)

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_article'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 5)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(published_article.pk))  # obvious

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_article'] = 1.0
        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_tutorial'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 5)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(published_tuto.pk))  # obvious

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_tutorial'] = 1.0
        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_opinion'] = 2.0
        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_opinion_not_picked'] = 4.0
        # Note: in "real life", unpicked opinion would get a boost < 1.

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 5)

        self.assertTrue(response[0].meta.score > response[1].meta.score > response[2].meta.score)
        self.assertEquals(response[0].meta.id, str(published_opinion_not_picked.pk))  # unpicked opinion got first
        self.assertEquals(response[1].meta.id, str(published_opinion_picked.pk))

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_opinion'] = 1.0
        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_opinion_not_picked'] = 1.0
        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_medium_or_big_tutorial'] = 2.0

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 5)

        self.assertTrue(response[0].meta.score > response[1].meta.score)
        self.assertEquals(response[0].meta.id, str(published_tuto.pk))  # obvious

        settings.ZDS_APP['search']['boosts']['publishedcontent']['if_medium_or_big_tutorial'] = 1.0

        # 6. Test global boosts
        # NOTE: score are NOT the same for all documents, no matter how hard it tries to, small differences exists

        for model in self.indexable:

            # set a huge number to overcome the small differences:
            settings.ZDS_APP['search']['boosts'][model.get_es_document_type()]['global'] = 10.0

            result = self.client.get(
                reverse('search:query') + '?q=' + text, follow=False)

            self.assertEqual(result.status_code, 200)
            response = result.context['object_list'].execute()
            self.assertEqual(response.hits.total, 10)

            self.assertEqual(response[0].meta.doc_type, model.get_es_document_type())  # obvious

            settings.ZDS_APP['search']['boosts'][model.get_es_document_type()]['global'] = 1.0

    def test_change_topic_impacts_posts(self):

        if not self.manager.connected_to_es:
            return

        # 1. Create an hidden forum belonging to an hidden group and add staff in it.
        text = 'test'

        group = Group.objects.create(name=u'Les illuminatis anonymes de ZdS')
        _, hidden_forum = create_category(group)

        self.staff.groups.add(group)
        self.staff.save()

        # 2. Create a normal topic and index it
        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.es_bulk_indexing_of_model(Topic)
        self.manager.es_bulk_indexing_of_model(Post)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 2)  # indexation ok

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 1)  # ok
        self.assertEqual(response[0].meta.doc_type, Post.get_es_document_type())
        self.assertEqual(response[0].forum_pk, self.forum.pk)
        self.assertEqual(response[0].topic_pk, topic_1.pk)
        self.assertEqual(response[0].topic_title, topic_1.title)

        # 3. Change topic title and reindex
        topic_1.title = 'new title'
        topic_1.save()

        self.manager.es_bulk_indexing_of_model(Topic)
        self.manager.es_bulk_indexing_of_model(Post)
        self.manager.refresh_index()

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 1)  # ok

        self.assertEqual(response[0].topic_title, topic_1.title)  # title was changed

        # 4. connect with staff and move topic
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))

        data = {
            'move': '',
            'forum': hidden_forum.pk,
            'topic': topic_1.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)

        self.manager.es_bulk_indexing_of_model(Topic)
        self.manager.es_bulk_indexing_of_model(Post)
        self.manager.refresh_index()

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 1)  # Note: without staff, would not get any results (see below)

        self.assertEqual(response[0].forum_pk, hidden_forum.pk)  # post was updated with new forum

        # 5. Topic is now hidden
        self.client.logout()

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=' + Post.get_es_document_type(), follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context['object_list'].execute()
        self.assertEqual(response.hits.total, 0)  # ok

    def test_change_publishedcontents_impacts_chapter(self):

        if not self.manager.connected_to_es:
            return

        # 1. Create middle tuto and index it
        text = 'test'

        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto_draft = tuto.load_version()

        tuto.title = text
        tuto.authors.add(self.user)
        tuto.save()

        tuto_draft.repo_update_top_container(text, tuto.slug, text, text)  # change title to be sure it will match

        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        chapter1.repo_update(text, text, text)
        extract = ExtractFactory(container=chapter1, db_object=tuto)
        extract.repo_update(text, text)

        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published
        tuto.save()

        self.manager.es_bulk_indexing_of_model(PublishedContent)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 2)  # indexation ok

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context['object_list'].execute()

        self.assertEqual(response.hits.total, 2)

        chapters = [r for r in response if r.meta.doc_type == 'chapter']
        self.assertEqual(chapters[0].meta.doc_type, FakeChapter.get_es_document_type())
        self.assertEqual(chapters[0].meta.id, published.content_public_slug + '__' + chapter1.slug)

        # 2. Change tuto : delete chapter and insert new one !
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        tuto_draft = tuto.load_version()

        tuto_draft.children[0].repo_delete()  # chapter 1 is gone !

        another_text = 'another thing'
        self.assertTrue(text not in another_text)  # to prevent a future modification from breaking this test

        chapter2 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        chapter2.repo_update(another_text, another_text, another_text)
        extract2 = ExtractFactory(container=chapter2, db_object=tuto)
        extract2.repo_update(another_text, another_text)

        published = publish_content(tuto, tuto_draft, is_major_update=False)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published
        tuto.save()

        self.manager.es_bulk_indexing_of_model(PublishedContent)
        self.manager.refresh_index()

        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 2)  # 2 objects, not 3 !

        result = self.client.get(
            reverse('search:query') + '?q=' + text + '&models=content', follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context['object_list'].execute()

        contents = [r for r in response if r.meta.doc_type != 'chapter']
        self.assertEqual(response.hits.total, len(contents))  # no chapter found anymore

        result = self.client.get(
            reverse('search:query') + '?q=' + another_text + '&models=content',
            follow=False
        )

        self.assertEqual(result.status_code, 200)

        response = result.context['object_list'].execute()
        chapters = [r for r in response if r.meta.doc_type == 'chapter']
        self.assertEqual(response.hits.total, 1)
        self.assertEqual(chapters[0].meta.doc_type, FakeChapter.get_es_document_type())
        self.assertEqual(chapters[0].meta.id, published.content_public_slug + '__' + chapter2.slug)  # got new chapter

    def test_opensearch(self):

        result = self.client.get(
            reverse('search:opensearch'),
            follow=False
        )

        self.assertEqual(result.status_code, 200)

        self.assertContains(result, reverse('search:query'))
        self.assertContains(result, reverse('search:opensearch'))

    def test_upercase_and_lowercase_search_give_same_results(self):
        """Pretty self-explanatory function name, isn't it ?"""

        if not self.manager.connected_to_es:
            return

        # 1. Index lowercase stuffs
        text_lc = 'test'

        topic_1_lc = TopicFactory(forum=self.forum, author=self.user, title=text_lc)

        tag_lc = TagFactory(title=text_lc)
        topic_1_lc.tags.add(tag_lc)
        topic_1_lc.subtitle = text_lc
        topic_1_lc.save()

        post_1_lc = PostFactory(topic=topic_1_lc, author=self.user, position=1)
        post_1_lc.text = post_1_lc.text_html = text_lc
        post_1_lc.save()

        tuto_lc = PublishableContentFactory(type='TUTORIAL')
        tuto_draft_lc = tuto_lc.load_version()

        tuto_lc.title = text_lc
        tuto_lc.authors.add(self.user)
        subcategory_lc = SubCategoryFactory(title=text_lc)
        tuto_lc.subcategory.add(subcategory_lc)
        tuto_lc.tags.add(tag_lc)
        tuto_lc.save()

        tuto_draft_lc.description = text_lc
        tuto_draft_lc.repo_update_top_container(text_lc, tuto_lc.slug, text_lc, text_lc)

        chapter1_lc = ContainerFactory(parent=tuto_draft_lc, db_object=tuto_lc)
        extract_lc = ExtractFactory(container=chapter1_lc, db_object=tuto_lc)
        extract_lc.repo_update(text_lc, text_lc)

        published_lc = publish_content(tuto_lc, tuto_draft_lc, is_major_update=True)

        tuto_lc.sha_public = tuto_draft_lc.current_version
        tuto_lc.sha_draft = tuto_draft_lc.current_version
        tuto_lc.public_version = published_lc
        tuto_lc.save()

        # 2. Index uppercase stuffs
        text_uc = 'TEST'

        topic_1_uc = TopicFactory(forum=self.forum, author=self.user, title=text_uc)

        topic_1_uc.tags.add(tag_lc)  # Note: a constraint force tags title to be unique
        topic_1_uc.subtitle = text_uc
        topic_1_uc.save()

        post_1_uc = PostFactory(topic=topic_1_uc, author=self.user, position=1)
        post_1_uc.text = post_1_uc.text_html = text_uc
        post_1_uc.save()

        tuto_uc = PublishableContentFactory(type='TUTORIAL')
        tuto_draft_uc = tuto_uc.load_version()

        tuto_uc.title = text_uc
        tuto_uc.authors.add(self.user)
        tuto_uc.subcategory.add(subcategory_lc)
        tuto_uc.tags.add(tag_lc)
        tuto_uc.save()

        tuto_draft_uc.description = text_uc
        tuto_draft_uc.repo_update_top_container(text_uc, tuto_uc.slug, text_uc, text_uc)

        chapter1_uc = ContainerFactory(parent=tuto_draft_uc, db_object=tuto_uc)
        extract_uc = ExtractFactory(container=chapter1_uc, db_object=tuto_uc)
        extract_uc.repo_update(text_uc, text_uc)

        published_uc = publish_content(tuto_uc, tuto_draft_uc, is_major_update=True)

        tuto_uc.sha_public = tuto_draft_uc.current_version
        tuto_uc.sha_draft = tuto_draft_uc.current_version
        tuto_uc.public_version = published_uc
        tuto_uc.save()

        # 3. Index and search:
        self.assertEqual(len(self.manager.setup_search(Search().query(MatchAll())).execute()), 0)

        # index
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.es_bulk_indexing_of_model(model)
        self.manager.refresh_index()

        result = self.client.get(reverse('search:query') + '?q=' + text_lc, follow=False)
        self.assertEqual(result.status_code, 200)

        response_lc = result.context['object_list'].execute()
        self.assertEqual(response_lc.hits.total, 8)

        result = self.client.get(reverse('search:query') + '?q=' + text_uc, follow=False)
        self.assertEqual(result.status_code, 200)

        response_uc = result.context['object_list'].execute()
        self.assertEqual(response_uc.hits.total, 8)

        for responses in zip(response_lc, response_uc):  # we should get results in the same order !
            self.assertEqual(responses[0].meta.id, responses[1].meta.id)

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
