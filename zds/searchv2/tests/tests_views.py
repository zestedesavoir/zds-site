from zds import json_handler
import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import Group
from zds.forum.tests.factories import TopicFactory, PostFactory, Topic, Post, TagFactory
from zds.forum.tests.factories import create_category_and_forum

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.searchv2.models import SearchIndexManager
from zds.tutorialv2.tests.factories import (
    PublishableContentFactory,
    ContainerFactory,
    ExtractFactory,
    publish_content,
    PublishedContentFactory,
    SubCategoryFactory,
)
from zds.tutorialv2.models.database import PublishedContent, FakeChapter, PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents


@override_for_contents(SEARCH_ENABLED=True)
class ViewsTests(TutorialTestMixin, TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        settings.ZDS_APP["member"]["bot_account"] = self.mas.username

        self.category, self.forum = create_category_and_forum()

        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.manager = SearchIndexManager()
        self.indexable = [FakeChapter, PublishedContent, Topic, Post]

        self.manager.reset_index(self.indexable)

    def test_basic_search(self):
        """Basic search and filtering"""

        if not self.manager.connected_to_search_engine:
            return

        # 1. Index and test search:
        text = "test"

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        # create a middle-size content and publish it
        tuto = PublishableContentFactory(type="TUTORIAL")
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

        # nothing has been indexed yet:
        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)  # good!

        # index
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model)

        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]

        self.assertEqual(len(response), 4)  # get 4 results

        # 2. Test filtering:
        topic_1 = Topic.objects.get(pk=topic_1.pk)
        post_1 = Post.objects.get(pk=post_1.pk)
        published = PublishedContent.objects.get(pk=published.pk)

        ids = {
            "topic": [topic_1.search_engine_id],
            "post": [post_1.search_engine_id],
            "publishedcontent": [published.search_engine_id, published.content_public_slug + "__" + chapter1.slug],
        }

        for doc_type in settings.ZDS_APP["search"]["search_groups"]:
            result = self.client.get(reverse("search:query") + "?q=" + text + "&models=" + doc_type, follow=False)
            self.assertEqual(result.status_code, 200)

            response = result.context["object_list"]
            self.assertEqual(len(response), len(ids[doc_type]))  # get 1 result of each …
            for i, r in enumerate(response):
                self.assertIn(
                    r["collection"], settings.ZDS_APP["search"]["search_groups"][doc_type][1]
                )  # … and only of the right type …
                self.assertEqual(r["document"]["id"], ids[doc_type][i])  # … with the right id !

    def test_invalid_search(self):
        """Check if the request is *, all documents are not displayed"""
        result = self.client.get(reverse("search:query") + "?q=*", follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["object_list"]), 0)

    def test_get_similar_topics(self):
        """Get similar topics lists"""

        if not self.manager.connected_to_search_engine:
            return

        text = "Clem ne se mange pas"

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        text = "Clem est la meilleure mascotte"

        topic_2 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_2 = PostFactory(topic=topic_2, author=self.user, position=1)
        post_2.text = post_1.text_html = text
        post_2.save()

        # 1. Should not get any result
        result = self.client.get(reverse("search:similar") + "?q=est", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # index
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model)

        # 2. Should get exactly one result
        result = self.client.get(reverse("search:similar") + "?q=mange", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 1)

        # 2. Should get exactly two results
        result = self.client.get(reverse("search:similar") + "?q=Clem", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 2)

    def test_hidden_post_are_not_result(self):
        """Hidden posts should not show up in the search results"""

        if not self.manager.connected_to_search_engine:
            return

        # 1. Index and test search:
        text = "test"

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.indexing_of_model(Topic)
        self.manager.indexing_of_model(Post)

        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        post_1 = Post.objects.get(pk=post_1.pk)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["document"]["position"], post_1.position)
        self.assertEqual(response[0]["document"]["topic_pk"], post_1.topic.pk)

        # 2. Hide, reindex and search again:
        post_1.hide_comment_by_user(self.staff, "Un abus de pouvoir comme un autre ;)")

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 0)  # nothing in the results

    def test_hidden_forums_give_no_results_if_user_not_allowed(self):
        """Long name, isn't ?"""

        if not self.manager.connected_to_search_engine:
            return

        # 1. Create a hidden forum belonging to a hidden staff group.
        text = "test"

        group = Group.objects.create(name="Les illuminatis anonymes de ZdS")
        _, hidden_forum = create_category_and_forum(group)

        self.staff.groups.add(group)
        self.staff.save()

        topic_1 = TopicFactory(forum=hidden_forum, author=self.staff, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.indexing_of_model(Topic)
        self.manager.indexing_of_model(Post)

        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        # 2. search without connection and get not result
        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 0)

        # 3. Connect with user (not a member of the group), search, and get no result
        self.client.force_login(self.user)

        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 0)

        # 4. Connect with staff, search, and get the topic and the post
        self.client.logout()
        self.client.force_login(self.staff)

        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)  # ok !

    def test_boosts(self):
        """Check if boosts are doing their job"""

        if not self.manager.connected_to_search_engine:
            return

        # 1. Create topics (with identical titles), posts (with identical texts), an article and a tuto
        text = "test"

        topic_1_solved_sticky = TopicFactory(forum=self.forum, author=self.user)
        topic_1_solved_sticky.title = text
        topic_1_solved_sticky.subtitle = ""
        topic_1_solved_sticky.solved_by = self.user
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
        topic_2_locked.subtitle = ""
        topic_2_locked.is_locked = True
        topic_2_locked.save()

        post_3_ld_below_1 = PostFactory(topic=topic_2_locked, author=self.user, position=1)
        post_3_ld_below_1.text = post_3_ld_below_1.text_html = text
        post_3_ld_below_1.like = 2
        post_3_ld_below_1.dislike = 5  # l/d ratio below 1
        post_3_ld_below_1.save()

        tuto = PublishableContentFactory(type="TUTORIAL")
        tuto_draft = tuto.load_version()

        tuto.title = text
        tuto.authors.add(self.user)
        tuto.save()

        tuto_draft.repo_update_top_container(text, tuto.slug, text, text)

        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto)
        chapter1.repo_update(text, "Who cares ?", "Same here")
        ExtractFactory(container=chapter1, db_object=tuto)

        published_tuto = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published_tuto
        tuto.save()

        article = PublishedContentFactory(type="ARTICLE", title=text)
        published_article = PublishedContent.objects.get(content_pk=article.pk)

        opinion_not_picked = PublishedContentFactory(type="OPINION", title=text)
        published_opinion_not_picked = PublishedContent.objects.get(content_pk=opinion_not_picked.pk)

        opinion_picked = PublishedContentFactory(type="OPINION", title=text)
        opinion_picked.sha_picked = opinion_picked.sha_draft
        opinion_picked.date_picked = datetime.datetime.now()
        opinion_picked.save()

        published_opinion_picked = PublishedContent.objects.get(content_pk=opinion_picked.pk)

        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model)

        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 10)  # indexing ok

        # 2. Reset all boosts to 1
        for doc_type in settings.ZDS_APP["search"]["boosts"]:
            for key in settings.ZDS_APP["search"]["boosts"][doc_type]:
                settings.ZDS_APP["search"]["boosts"][doc_type][key] = 1.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        # 3. Test posts
        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        # score are equals without boost:
        self.assertTrue(
            response[0]["document"]["score"] == response[1]["document"]["score"] == response[2]["document"]["score"]
        )

        settings.ZDS_APP["search"]["boosts"]["post"]["if_first"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["score"] == response[1]["document"]["score"] > response[2]["document"]["score"]
        )
        self.assertEqual(response[2]["document"]["id"], str(post_2_useful.pk))  # post 2 is the only one not first

        settings.ZDS_APP["search"]["boosts"]["post"]["if_first"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["post"]["if_useful"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["score"] > response[1]["document"]["score"] == response[2]["document"]["score"]
        )
        self.assertEqual(response[0]["document"]["id"], str(post_2_useful.pk))  # post 2 is useful

        settings.ZDS_APP["search"]["boosts"]["post"]["if_useful"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_above_1"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["score"] == response[1]["document"]["score"] > response[2]["document"]["score"]
        )
        self.assertEqual(response[0]["document"]["id"], str(post_2_useful.pk))  # post 2 have a l/d ratio of 5/2

        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_above_1"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_below_1"] = 2.0  # no one would do that in real life

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["score"] > response[1]["document"]["score"] == response[2]["document"]["score"]
        )
        self.assertEqual(response[0]["document"]["id"], str(post_3_ld_below_1.pk))  # post 3 have a l/d ratio of 2/5

        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_below_1"] = 1.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        # 4. Test topics
        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        # score are equals without boost:
        self.assertTrue(response[0]["document"]["score"] == response[1]["document"]["score"])

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_sticky"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertTrue(response[0]["document"]["score"] > response[1]["document"]["score"])
        self.assertEqual(response[0]["document"]["id"], str(topic_1_solved_sticky.pk))  # topic 1 is sticky

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_sticky"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["topic"]["if_solved"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertTrue(response[0]["document"]["score"] > response[1]["document"]["score"])
        self.assertEqual(response[0]["document"]["id"], str(topic_1_solved_sticky.pk))  # topic 1 is solved

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_solved"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["topic"]["if_locked"] = 2.0  # no one would do that in real life

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertTrue(response[0]["document"]["score"] > response[1]["document"]["score"])
        self.assertEqual(response[0]["document"]["id"], str(topic_2_locked.pk))  # topic 2 is locked

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_locked"] = 1.0  # no one would do that in real life

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        # 5. Test published contents
        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        # score are equals without boost:
        self.assertTrue(
            response[0]["document"]["score"]
            == response[1]["document"]["score"]
            == response[2]["document"]["score"]
            == response[3]["document"]["score"]
        )

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_article"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(response[0]["document"]["score"] > response[1]["document"]["score"])
        self.assertEqual(response[0]["document"]["id"], str(published_article.pk))  # obvious

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_article"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_medium_or_big_tutorial"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(response[0]["document"]["score"] > response[1]["document"]["score"])
        self.assertEqual(response[0]["document"]["id"], str(published_tuto.pk))  # obvious

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_medium_or_big_tutorial"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion"] = 2.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion_not_picked"] = 4.0
        # Note: in "real life", unpicked opinion would get a boost < 1.

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(
            response[0]["document"]["score"] > response[1]["document"]["score"] > response[2]["document"]["score"]
        )
        self.assertEqual(
            response[0]["document"]["id"], str(published_opinion_not_picked.pk)
        )  # unpicked opinion got first
        self.assertEqual(response[1]["document"]["id"], str(published_opinion_picked.pk))

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion_not_picked"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_medium_or_big_tutorial"] = 2.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(response[0]["document"]["score"] > response[1]["document"]["score"])
        self.assertEqual(response[0]["document"]["id"], str(published_tuto.pk))  # obvious

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_medium_or_big_tutorial"] = 1.0

        # Reindex to update the score
        self.manager.reset_index(self.indexable)
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True)

        # 6. Test global boosts
        # NOTE: score are NOT the same for all documents, no matter how hard it tries to, small differences exists

        for model in self.indexable:
            # set a huge number to overcome the small differences:
            collection = model.get_document_type()
            for key in settings.ZDS_APP["search"]["boosts"][collection]:
                settings.ZDS_APP["search"]["boosts"][collection][key] = 10.0

            # Reindex to update the score
            self.manager.reset_index(self.indexable)
            for model in self.indexable:
                if model is FakeChapter:
                    continue
                self.manager.indexing_of_model(model, force_reindexing=True)

            result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)

            self.assertEqual(result.status_code, 200)
            response = result.context["object_list"]
            self.assertEqual(len(response), 10)

            self.assertEqual(response[0]["collection"], collection)  # obvious

            for key in settings.ZDS_APP["search"]["boosts"][collection]:
                settings.ZDS_APP["search"]["boosts"][collection][key] = 1

            # Reindex to update the score
            self.manager.reset_index(self.indexable)
            for model in self.indexable:
                if model is FakeChapter:
                    continue
                self.manager.indexing_of_model(model, force_reindexing=True)

    def test_change_topic_impacts_posts(self):
        if not self.manager.connected_to_search_engine:
            return

        # 1. Create a hidden forum belonging to a hidden group and add staff in it.
        text = "test"

        group = Group.objects.create(name="Les illuminatis anonymes de ZdS")
        _, hidden_forum = create_category_and_forum(group)

        self.staff.groups.add(group)
        self.staff.save()

        # 2. Create a normal topic and index it
        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.indexing_of_model(Topic)
        self.manager.indexing_of_model(Post)

        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 1)  # ok
        self.assertEqual(response[0]["collection"], Post.get_document_type())
        self.assertEqual(response[0]["document"]["forum_pk"], self.forum.pk)
        self.assertEqual(response[0]["document"]["topic_pk"], topic_1.pk)
        self.assertEqual(response[0]["document"]["topic_title"], topic_1.title)

        # 3. Change topic title and reindex
        topic_1.title = "new title"
        topic_1.save()

        self.manager.reset_index([Topic, Post])
        self.manager.indexing_of_model(Topic, force_reindexing=True)
        self.manager.indexing_of_model(Post, force_reindexing=True)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 1)  # ok

        self.assertEqual(response[0]["document"]["topic_title"], topic_1.title)  # title was changed

        # 4. connect with staff and move topic
        self.client.force_login(self.staff)

        data = {"move": "", "forum": hidden_forum.pk, "topic": topic_1.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)

        self.manager.reset_index([Topic, Post])
        self.manager.indexing_of_model(Topic)
        self.manager.indexing_of_model(Post)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 1)  # Note: without staff, would not get any results (see below)

        self.assertEqual(response[0]["document"]["forum_pk"], hidden_forum.pk)  # post was updated with new forum

        # 5. Topic is now hidden
        self.client.logout()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 0)  # ok

    def test_change_publishedcontents_impacts_chapter(self):
        if not self.manager.connected_to_search_engine:
            return

        # 1. Create middle-size content and index it
        text = "test"

        tuto = PublishableContentFactory(type="TUTORIAL")
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

        self.manager.indexing_of_model(PublishedContent)

        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]

        self.assertEqual(len(response), 2)

        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)
        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]

        chapters = [r for r in response if r["collection"] == "chapter"]
        self.assertEqual(chapters[0]["collection"], FakeChapter.get_document_type())
        self.assertEqual(chapters[0]["document"]["id"], published.content_public_slug + "__" + chapter1.slug)

        # 2. Change tuto: delete chapter and insert new one !
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        tuto_draft = tuto.load_version()

        tuto_draft.children[0].repo_delete()  # chapter 1 is gone !

        another_text = "another thing"
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

        self.manager.reset_index([PublishedContent, FakeChapter])
        self.manager.indexing_of_model(PublishedContent, force_reindexing=True)
        self.manager.indexing_of_model(FakeChapter)

        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]

        contents = [r for r in response if r["collection"] != "chapter"]
        self.assertEqual(len(response), len(contents))  # no chapter found anymore

        result = self.client.get(reverse("search:query") + "?q=" + another_text, follow=False)

        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]
        chapters = [r for r in response if r["collection"] == "chapter"]
        self.assertEqual(len(response), 1)
        self.assertEqual(chapters[0]["collection"], FakeChapter.get_document_type())
        self.assertEqual(
            chapters[0]["document"]["id"], published.content_public_slug + "__" + chapter2.slug
        )  # got new chapter

    def test_opensearch(self):
        result = self.client.get(reverse("search:opensearch"), follow=False)

        self.assertEqual(result.status_code, 200)

        self.assertContains(result, reverse("search:query"))
        self.assertContains(result, reverse("search:opensearch"))

    def test_upercase_and_lowercase_search_give_same_results(self):
        """Pretty self-explanatory function name, isn't it ?"""

        if not self.manager.connected_to_search_engine:
            return

        # 1. Index lowercase stuffs
        text_lc = "test"

        topic_1_lc = TopicFactory(forum=self.forum, author=self.user, title=text_lc)

        tag_lc = TagFactory(title=text_lc)
        topic_1_lc.tags.add(tag_lc)
        topic_1_lc.subtitle = text_lc
        topic_1_lc.save()

        post_1_lc = PostFactory(topic=topic_1_lc, author=self.user, position=1)
        post_1_lc.text = post_1_lc.text_html = text_lc
        post_1_lc.save()

        tuto_lc = PublishableContentFactory(type="TUTORIAL")
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
        text_uc = "TEST"

        topic_1_uc = TopicFactory(forum=self.forum, author=self.user, title=text_uc)

        topic_1_uc.tags.add(tag_lc)  # Note: a constraint forces tags title to be unique
        topic_1_uc.subtitle = text_uc
        topic_1_uc.save()

        post_1_uc = PostFactory(topic=topic_1_uc, author=self.user, position=1)
        post_1_uc.text = post_1_uc.text_html = text_uc
        post_1_uc.save()

        tuto_uc = PublishableContentFactory(type="TUTORIAL")
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
        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)  # indexing ok

        # index
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model)

        result = self.client.get(reverse("search:query") + "?q=" + text_lc, follow=False)
        self.assertEqual(result.status_code, 200)

        response_lc = result.context["object_list"]
        self.assertEqual(len(response_lc), 8)

        result = self.client.get(reverse("search:query") + "?q=" + text_uc, follow=False)
        self.assertEqual(result.status_code, 200)

        response_uc = result.context["object_list"]
        self.assertEqual(len(response_uc), 8)

        for responses in zip(response_lc, response_uc):  # we should get results in the same order!
            self.assertEqual(responses[0]["document"]["id"], responses[1]["document"]["id"])

    def test_category_and_subcategory_impact_search(self):
        """If two contents do not belong to the same (sub)category"""

        if not self.manager.connected_to_search_engine:
            return

        text = "Did you ever hear the tragedy of Darth Plagueis The Wise?"

        # 1. Create two contents with different subcategories
        category_1 = "category 1"
        subcategory_1 = SubCategoryFactory(title=category_1)
        category_2 = "category 2"
        subcategory_2 = SubCategoryFactory(title=category_2)

        tuto_1 = PublishableContentFactory(type="TUTORIAL")
        tuto_1_draft = tuto_1.load_version()

        tuto_1.title = text
        tuto_1.authors.add(self.user)
        tuto_1.subcategory.add(subcategory_1)
        tuto_1.save()

        tuto_1_draft.description = text
        tuto_1_draft.repo_update_top_container(text, tuto_1.slug, text, text)

        chapter_1 = ContainerFactory(parent=tuto_1_draft, db_object=tuto_1)
        extract_1 = ExtractFactory(container=chapter_1, db_object=tuto_1)
        extract_1.repo_update(text, text)

        published_1 = publish_content(tuto_1, tuto_1_draft, is_major_update=True)

        tuto_1.sha_public = tuto_1_draft.current_version
        tuto_1.sha_draft = tuto_1_draft.current_version
        tuto_1.public_version = published_1
        tuto_1.save()

        tuto_2 = PublishableContentFactory(type="TUTORIAL")
        tuto_2_draft = tuto_2.load_version()

        tuto_2.title = text
        tuto_2.authors.add(self.user)
        tuto_2.subcategory.add(subcategory_2)
        tuto_2.save()

        tuto_2_draft.description = text
        tuto_2_draft.repo_update_top_container(text, tuto_2.slug, text, text)

        chapter_2 = ContainerFactory(parent=tuto_2_draft, db_object=tuto_2)
        extract_2 = ExtractFactory(container=chapter_2, db_object=tuto_2)
        extract_2.repo_update(text, text)

        published_2 = publish_content(tuto_2, tuto_2_draft, is_major_update=True)

        tuto_2.sha_public = tuto_2_draft.current_version
        tuto_2.sha_draft = tuto_2_draft.current_version
        tuto_2.public_version = published_2
        tuto_2.save()

        # 2. Index:
        results = self.manager.setup_search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)  # indexing ok

        # index
        for model in self.indexable:
            self.manager.indexing_of_model(model)

        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]
        self.assertEqual(len(response), 4)  # Ok

        # 3. Test
        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&subcategory=" + subcategory_1.slug,
            follow=False,
        )

        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertEqual(
            [int(r["document"]["id"]) for r in response if r["collection"] == "publishedcontent"][0], published_1.pk
        )
        self.assertEqual(
            [r["document"]["id"] for r in response if r["collection"] == "chapter"][0],
            tuto_1.slug + "__" + chapter_1.slug,
        )

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&subcategory=" + subcategory_2.slug,
            follow=False,
        )

        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertEqual(
            [int(r["document"]["id"]) for r in response if r["collection"] == "publishedcontent"][0], published_2.pk
        )
        self.assertEqual(
            [r["document"]["id"] for r in response if r["collection"] == "chapter"][0],
            tuto_2.slug + "__" + chapter_2.slug,
        )

    def tearDown(self):
        super().tearDown()

        # delete index:
        self.manager.clear_index()
