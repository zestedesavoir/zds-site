from copy import deepcopy

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test.utils import override_settings

from zds.forum.tests.factories import (
    Post,
    PostFactory,
    TagFactory,
    Topic,
    TopicFactory,
    create_category_and_forum,
    create_topic_in_forum,
)
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.search.utils import SearchIndexManager
from zds.tutorialv2.models.database import FakeChapter, PublishableContent, PublishedContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ExtractFactory,
    PublishableContentFactory,
    PublishedContentFactory,
    publish_content,
)
from zds.utils.tests.factories import CategoryFactory, SubCategoryFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["extra_content_generation_policy"] = "NONE"
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"


@override_settings(ZDS_APP=overridden_zds_app)
@override_for_contents(SEARCH_ENABLED=True)
class SearchIndexManagerTests(TutorialTestMixin, TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        settings.ZDS_APP["member"]["bot_account"] = self.mas.username

        self.category, self.forum = create_category_and_forum()

        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.manager = SearchIndexManager()
        self.indexable = [FakeChapter, PublishedContent, Topic, Post]

        self.manager.reset_index()

    def test_setup_functions(self):
        """Test the behavior of the reset_index() and clear_index() functions"""

        if not self.manager.connected:
            return

        # 1. Creation:
        models = [Topic, Post]
        self.manager.reset_index()

        # test collection
        for model in models:
            self.assertTrue(model.get_search_document_type() in self.manager.collections)

        # 2. Clearing
        self.manager.clear_index()
        self.assertTrue(len(self.manager.collections) == 0)  # back to the void

    def test_indexation(self):
        """test the indexation and deletion of the different documents"""

        if not self.manager.connected:
            return

        # create a topic with a post
        topic = TopicFactory(forum=self.forum, author=self.user)
        post = PostFactory(topic=topic, author=self.user, position=1)

        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(pk=post.pk)

        self.assertTrue(topic.search_engine_requires_index)
        self.assertTrue(post.search_engine_requires_index)

        # create a middle-tutorial and publish it
        tuto = PublishableContentFactory(type="TUTORIAL")
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
        self.assertTrue(published.search_engine_requires_index)

        # 1. index all
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=False)

        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(pk=post.pk)

        self.assertFalse(topic.search_engine_requires_index)
        self.assertFalse(post.search_engine_requires_index)

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertFalse(published.search_engine_requires_index)

        results = self.manager.search("*")  # get all documents
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 4)  # get 4 results, one of each type

        must_contain = {"post": False, "topic": False, "publishedcontent": False, "chapter": False}
        id_must_be = {
            "post": str(post.pk),
            "topic": str(topic.pk),
            "publishedcontent": str(published.pk),
            "chapter": tuto.slug + "__" + chapter1.slug,
        }

        for result in results:
            doc_type = result["request_params"]["collection_name"]
            must_contain[doc_type] = True
            for hit in result["hits"]:
                doc_id = hit["document"]["id"]
                self.assertEqual(doc_id, id_must_be[doc_type])

        self.assertTrue(all(must_contain))

        # 2. Test what reindexation will do:
        new_topic = TopicFactory(forum=self.forum, author=self.user)
        new_post = PostFactory(topic=new_topic, author=self.user, position=1)

        pk_of_topics_to_reindex = []
        for item in Topic.get_indexable(force_reindexing=False):
            pk_of_topics_to_reindex.append(item.pk)

        pk_of_posts_to_reindex = []
        for item in Post.get_indexable(force_reindexing=False):
            pk_of_posts_to_reindex.append(item.pk)

        self.assertTrue(topic.pk not in pk_of_topics_to_reindex)
        self.assertTrue(new_topic.pk in pk_of_topics_to_reindex)
        self.assertTrue(post.pk not in pk_of_posts_to_reindex)
        self.assertTrue(new_post.pk in pk_of_posts_to_reindex)

        for model in self.indexable:  # ok, so let's index that
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=False)

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 6)  # good!

        # 3. Test single deletion:
        new_post = Post.objects.get(pk=new_post.pk)

        self.manager.delete_document(new_post)

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 5)  # one is missing

        for result in results:
            doc_type = result["request_params"]["collection_name"]
            for hit in result["hits"]:
                doc_id = hit["document"]["id"]
                self.assertTrue(doc_type != Post.get_search_document_type() or doc_id != new_post.search_engine_id)

        # 4. Test "delete_by_query_deletion":
        topic = Topic.objects.get(pk=topic.pk)
        new_topic = Topic.objects.get(pk=new_topic.pk)

        self.manager.delete_by_query(
            Topic.get_search_document_type(),
            {"filter_by": f"id:= [{topic.search_engine_id}, {new_topic.search_engine_id}]"},
        )  # the two topic are deleted

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 3)

        for result in results:
            doc_type = result["request_params"]["collection_name"]
            for hit in result["hits"]:
                doc_id = hit["document"]["id"]
                self.assertTrue(doc_type != Topic.get_search_document_type() or doc_id != new_topic.search_engine_id)
                self.assertTrue(doc_type != Topic.get_search_document_type() or doc_id != topic.search_engine_id)

        # 5. Test that the deletion of an object also triggers its deletion in Typesense
        post = Post.objects.get(pk=post.pk)
        post.delete()

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)

        for result in results:
            doc_type = result["request_params"]["collection_name"]
            for hit in result["hits"]:
                doc_id = hit["document"]["id"]
                self.assertTrue(doc_type != Post.get_search_document_type() or doc_id != post.search_engine_id)

        # 6. Test full desindexation:
        self.manager.reset_index()

        # note "topic" is gone since "post" is gone, due to relationships at the Django level
        new_topic = Topic.objects.get(pk=new_topic.pk)
        new_post = Post.objects.get(pk=new_post.pk)

        self.assertTrue(new_topic.search_engine_requires_index)
        self.assertTrue(new_post.search_engine_requires_index)

        published = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertTrue(published.search_engine_requires_index)

    def test_special_case_of_contents(self):
        """test that the old publishedcontent does not stay when a new one is created"""

        if not self.manager.connected:
            return

        # 1. Create a middle-tutorial, publish it, then index it
        tuto = PublishableContentFactory(type="TUTORIAL")
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

        self.manager.indexing_of_model(PublishedContent, force_reindexing=True, verbose=False)  # index

        first_publication = PublishedContent.objects.get(content_pk=tuto.pk)
        self.assertFalse(first_publication.search_engine_requires_index)

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # get 2 results, one for the content and one for the chapter

        self.assertEqual(PublishedContent.objects.count(), 1)

        # 2. Change thet title, which will trigger a change in the slug
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version(sha=tuto.sha_draft)

        tuto.title = "un titre complètement différent!"
        tuto.save(force_slug_update=True)

        versioned.repo_update_top_container(tuto.title, tuto.slug, "osef", "osef")
        second_publication = publish_content(tuto, versioned, True)

        tuto.sha_public = versioned.current_version
        tuto.sha_draft = versioned.current_version
        tuto.public_version = second_publication
        tuto.save()

        self.assertEqual(PublishedContent.objects.count(), 2)  # now there is two objects ...
        first_publication = PublishedContent.objects.get(pk=first_publication.pk)
        self.assertTrue(first_publication.must_redirect)  # .. including the first one, for redirection

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)  # the old one is gone (and we need to reindex to get the new one)

        # 3. Check if indexation brings the new one, and not the old one
        self.manager.indexing_of_model(PublishedContent, force_reindexing=True, verbose=False)  # index

        first_publication = PublishedContent.objects.get(pk=first_publication.pk)
        second_publication = PublishedContent.objects.get(pk=second_publication.pk)

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # Still 2, not 4 !

        found_old = False
        found_new = False

        for result in results:
            doc_type = result["request_params"]["collection_name"]
            for hit in result["hits"]:
                doc_id = hit["document"]["id"]
                if doc_type == PublishedContent.get_search_document_type():
                    if doc_id == first_publication.search_engine_id:
                        found_old = True
                    if doc_id == second_publication.search_engine_id:
                        found_new = True

        self.assertTrue(found_new)
        self.assertFalse(found_old)

    def test_update_topic(self):
        """test that changing an attribute of a topic marks it as to index"""

        if not self.manager.connected:
            return

        group = Group.objects.create(name="DummyGroup_1")
        self.user.groups.add(group)
        self.user.save()

        _, other_forum = create_category_and_forum()
        _, private_forum = create_category_and_forum(group)

        other_topic = TopicFactory(forum=other_forum, author=self.user)
        other_topic.save(search_engine_requires_index=False)

        topic = TopicFactory(forum=self.forum, author=self.user)
        topic.save(search_engine_requires_index=False)

        private_topic = TopicFactory(forum=self.forum, author=self.user)
        private_topic.save(search_engine_requires_index=True)

        # index all topics
        self.manager.indexing_of_model(Topic, force_reindexing=False)
        results = self.manager.search("*")  # get all documents
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 1)

        # Move the private topic to a private forum
        private_topic = Topic.objects.get(pk=private_topic.pk)  # to get the search_engine_id
        private_topic.forum = private_forum
        private_topic.save()
        private_topic.refresh_from_db()
        self.assertTrue(private_topic.search_engine_requires_index)
        # the topic was removed from the search engine:
        results = self.manager.search("*")  # get all documents
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)

        # Rename the forum (changes forum_title)
        topic.save(search_engine_requires_index=False)
        self.forum.title = "Other title"
        self.forum.save()
        topic.refresh_from_db()
        self.assertTrue(topic.search_engine_requires_index)

        # Move the topic to another forum (changes forum_pk and forum_title)
        topic.save(search_engine_requires_index=False)
        topic.forum = other_forum
        topic.save()
        topic.refresh_from_db()
        self.assertTrue(topic.search_engine_requires_index)

        # Update title:
        topic.save(search_engine_requires_index=False)
        topic.title = "Changed title"
        topic.save()
        self.assertTrue(topic.search_engine_requires_index)

        # Update subtitle:
        topic.save(search_engine_requires_index=False)
        topic.subtitle = "Changed subtitle"
        topic.save()
        self.assertTrue(topic.search_engine_requires_index)

        # Add a tag:
        topic.save(search_engine_requires_index=False)
        tag = TagFactory()
        tag.save()
        topic.tags.add(tag)
        topic.save()
        self.assertTrue(topic.search_engine_requires_index)

        # Rename the tag:
        topic.save(search_engine_requires_index=False)
        tag.title = "New tag"
        tag.save()
        topic.refresh_from_db()
        self.assertTrue(topic.search_engine_requires_index)

        # Change the locked status
        topic.save(search_engine_requires_index=False)
        topic.is_locked = not topic.is_locked
        topic.save()
        topic.refresh_from_db()
        self.assertTrue(topic.search_engine_requires_index)

        # Change the solved status
        topic.save(search_engine_requires_index=False)
        topic.solved_by = self.user
        topic.save()
        topic.refresh_from_db()
        self.assertTrue(topic.search_engine_requires_index)

        # Change the sticky status
        topic.save(search_engine_requires_index=False)
        topic.is_sticky = not topic.is_sticky
        topic.save()
        topic.refresh_from_db()
        self.assertTrue(topic.search_engine_requires_index)

        # It did not impact other topics:
        other_topic.refresh_from_db()
        self.assertFalse(other_topic.search_engine_requires_index)

    def test_update_post(self):
        """test that changing an attribute of a post marks it as to index"""

        if not self.manager.connected:
            return

        group = Group.objects.create(name="DummyGroup_1")
        self.user.groups.add(group)
        self.user.save()

        _, other_forum = create_category_and_forum()
        _, private_forum = create_category_and_forum(group)

        private_topic = TopicFactory(forum=self.forum, author=self.user)
        private_topic.save(search_engine_requires_index=True)
        private_post = PostFactory(topic=private_topic, author=self.user, position=2)
        private_post.save(search_engine_requires_index=True)

        topic = create_topic_in_forum(self.forum, self.user.profile)
        topic.save(search_engine_requires_index=False)
        post = PostFactory(topic=topic, author=self.user, position=2)
        post.save(search_engine_requires_index=False)

        other_topic = create_topic_in_forum(self.forum, self.user.profile)
        other_topic.save(search_engine_requires_index=False)
        other_post = PostFactory(topic=other_topic, author=self.user, position=2)
        other_post.save(search_engine_requires_index=False)

        # index all posts
        self.manager.indexing_of_model(Post, force_reindexing=False)
        results = self.manager.search("*")  # get all documents
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 3)

        # Move the topic to a private forum, so it becomes a private topic
        # (this also tests we can move a topic to a private forum before it was even indexed)
        private_topic.forum = private_forum
        private_topic.save()
        private_topic.refresh_from_db()
        self.assertTrue(private_topic.search_engine_requires_index)
        # the post was removed from the search engine:
        results = self.manager.search("*")  # get all documents
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)

        # Move the topic to another forum (changes forum_pk)
        post.save(search_engine_requires_index=False)
        post.topic.forum = other_forum
        post.topic.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # Change the topic title (changes topic_title)
        post.save(search_engine_requires_index=False)
        post.topic.title = "Changed title"
        post.topic.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # Change the forum title (changes forum_title)
        post.save(search_engine_requires_index=False)
        post.topic.forum.title = "Changed title"
        post.topic.forum.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # Change the content
        post.save(search_engine_requires_index=False)
        post.text = "New text"
        post.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # Mark it as useful
        post.save(search_engine_requires_index=False)
        post.is_useful = not post.is_useful
        post.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # Like it
        post.save(search_engine_requires_index=False)
        post.like += 1
        post.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # Dislike it
        post.save(search_engine_requires_index=False)
        post.dislike += 1
        post.save()
        post.refresh_from_db()
        self.assertTrue(post.search_engine_requires_index)

        # It did not impact other posts:
        other_post.refresh_from_db()
        self.assertFalse(other_post.search_engine_requires_index)

    def test_update_published_content(self):
        """
        Test that changing an attribute of a published content marks it as to
        index.

        No need to test the update of FakeChapter, since the reindex of a
        published content starts by removing all its fake chapters from the
        search engine.
        """

        if not self.manager.connected:
            return

        published_content = PublishedContentFactory().public_version
        published_content.save(search_engine_requires_index=False)

        other_published_content = PublishedContentFactory().public_version
        other_published_content.save(search_engine_requires_index=False)

        tag = TagFactory()
        tag.save()

        category = CategoryFactory()
        category.save()

        subcategory = SubCategoryFactory(category=category)
        subcategory.save()

        # Add a tag
        published_content.save(search_engine_requires_index=False)
        published_content.content.tags.add(tag)
        published_content.content.save()
        published_content.refresh_from_db()
        self.assertTrue(published_content.search_engine_requires_index)

        # Rename the tag
        published_content.save(search_engine_requires_index=False)
        tag.title = "New tag"
        tag.save()
        published_content.refresh_from_db()
        self.assertTrue(published_content.search_engine_requires_index)

        # Add a subcategory
        published_content.save(search_engine_requires_index=False)
        published_content.content.subcategory.add(subcategory)
        published_content.content.save()
        published_content.refresh_from_db()
        self.assertTrue(published_content.search_engine_requires_index)

        # Rename the subcategory
        published_content.save(search_engine_requires_index=False)
        subcategory.title = "New subcategory"
        subcategory.save()
        published_content.refresh_from_db()
        self.assertTrue(published_content.search_engine_requires_index)

        # Rename the category
        published_content.save(search_engine_requires_index=False)
        category.title = "New category"
        category.save()
        published_content.refresh_from_db()
        self.assertTrue(published_content.search_engine_requires_index)

        # It did not impact other contents:
        other_published_content.refresh_from_db()
        self.assertFalse(other_published_content.search_engine_requires_index)

    def tearDown(self):
        super().tearDown()

        # delete index:
        self.manager.clear_index()
