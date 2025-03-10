import datetime
from copy import deepcopy
from math import ceil

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from zds import json_handler
from zds.forum.tests.factories import Post, PostFactory, TagFactory, Topic, TopicFactory, create_category_and_forum
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.search.utils import SearchIndexManager
from zds.tutorialv2.models.database import FakeChapter, PublishableContent, PublishedContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ExtractFactory,
    PublishableContentFactory,
    PublishedContentFactory,
    SubCategoryFactory,
    publish_content,
)

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["extra_content_generation_policy"] = "NONE"
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"


@override_settings(ZDS_APP=overridden_zds_app)
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

        self.manager.reset_index()

    def _index_everything(self):
        self.manager.reset_index()
        for model in self.indexable:
            if model is FakeChapter:
                continue
            self.manager.indexing_of_model(model, force_reindexing=True, verbose=False)

    def test_basic_search(self):
        """Basic search and filtering"""

        if not self.manager.connected:
            return

        tag = TagFactory(title="Clémentine à pépins")  # with accents to make a different slug

        # 1. Index and test search:
        text = "test"

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        topic_1.tags.add(tag)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        # create a middle-size content and publish it
        tuto = PublishableContentFactory(type="TUTORIAL")
        tuto_draft = tuto.load_version()

        tuto.tags.add(tag)
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
        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)  # good!

        # index
        self._index_everything()

        result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)
        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]

        self.assertEqual(len(response), 4)  # get 4 results

        # Ugly hack to search only in search results. In the menu in the
        # header, the last tags are showed, but this section is cached:
        # depending on which tests are launched and in which order, the menu
        # may contain or not these tags.
        content_search_results = result.content.decode()[result.content.decode().find("search-results") :]
        # The tag appears 2 times: in two search results
        self.assertEqual(content_search_results.count(tag.title), 2)
        self.assertEqual(content_search_results.count(tag.slug), 2)

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

        # Search with a query which returns results, but without highlights:
        result = self.client.get(reverse("search:query") + "?q=-c", follow=False)
        self.assertEqual(result.status_code, 200)

    def test_search_many_pages(self):
        if not self.manager.connected:
            return

        text = "foo"
        url = reverse("search:query") + "?q=" + text
        results_per_page = settings.ZDS_APP["search"]["results_per_page"]

        # 1. There are less than 250 results per collection
        nb_topics = 150
        nb_pages = ceil(2 * nb_topics / results_per_page)

        for i in range(nb_topics):
            topic = TopicFactory(forum=self.forum, author=self.user, title=text)
            post = PostFactory(topic=topic, author=self.user, position=1)
            post.text = post.text_html = text
            post.save()

        self._index_everything()

        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["paginator"].num_pages, nb_pages)
        self.assertEqual(len(result.context["object_list"]), results_per_page)

        result = self.client.get(f"{url}&page={nb_pages}", follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["object_list"]), 2 * nb_topics - (nb_pages - 1) * results_per_page)
        self.assertFalse(result.context["has_more_results"])

        # 2. There are more than 250 results per collection
        nb_pages = ceil(2 * min(2 * nb_topics, 250) / results_per_page)

        # Append 150 new topics, making it > 250
        for i in range(nb_topics):
            topic = TopicFactory(forum=self.forum, author=self.user, title=text)
            post = PostFactory(topic=topic, author=self.user, position=1)
            post.text = post.text_html = text
            post.save()

        self._index_everything()

        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["paginator"].num_pages, nb_pages)
        self.assertEqual(len(result.context["object_list"]), results_per_page)

        result = self.client.get(f"{url}&page={nb_pages}", follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["object_list"]), results_per_page)
        self.assertTrue(result.context["has_more_results"])

    def test_invalid_search(self):
        if not self.manager.connected:
            return

        # Check if the request is *, no result is displayed
        result = self.client.get(reverse("search:query") + "?q=*", follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["object_list"]), 0)

        # Check if there is no query parametern there is no error:
        result = self.client.get(reverse("search:query"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["object_list"]), 0)

        # Check if the request contains an invalid models field:
        result = self.client.get(reverse("search:query") + "?q=latex&models=", follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["object_list"]), 0)

    def test_get_similar_topics(self):
        """Get similar topics lists"""

        if not self.manager.connected:
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

        # Create a hidden forum with a matching topic that should not show up
        group = Group.objects.create(name="Les illuminatis anonymes de ZdS")
        _, hidden_forum = create_category_and_forum(group)

        topic_hidden = TopicFactory(forum=hidden_forum, author=self.staff, title=text)
        post_hidden = PostFactory(topic=topic_hidden, author=self.user, position=1)
        post_hidden.text = post_hidden.text_html = text
        post_hidden.save()

        # Should not get any result
        result = self.client.get(reverse("search:similar") + "?q=est", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # Should not get a 500 if collections do not exist:
        self.manager.clear_index()
        result = self.client.get(reverse("search:similar") + "?q=mange", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # create collections and index content:
        self._index_everything()

        # Should get exactly one result
        result = self.client.get(reverse("search:similar") + "?q=mange", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 1)

        # Should get exactly two results
        result = self.client.get(reverse("search:similar") + "?q=Clem", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 2)

        # Should not get any result:
        result = self.client.get(reverse("search:similar") + "?q=*", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

    def test_hidden_post_are_not_in_results(self):
        """Hidden posts should not show up in the search results"""

        if not self.manager.connected:
            return

        # 1. Index and test search:
        text = "test"

        topic_1 = TopicFactory(forum=self.forum, author=self.user, title=text)
        post_1 = PostFactory(topic=topic_1, author=self.user, position=1)
        post_1.text = post_1.text_html = text
        post_1.save()

        self.manager.indexing_of_model(Topic)
        self.manager.indexing_of_model(Post)

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        post_1 = Post.objects.get(pk=post_1.pk)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)

        response = result.context["object_list"]

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["document"]["get_absolute_url"], post_1.get_absolute_url())
        self.assertEqual(response[0]["document"]["topic_pk"], post_1.topic.pk)

        # 2. Hide, reindex and search again:
        post_1.hide_comment_by_user(self.staff, "Un abus de pouvoir comme un autre ;)")

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 0)  # nothing in the results

    def test_hidden_forums_give_no_results_if_user_not_allowed(self):
        """Long name, isn't ?"""

        if not self.manager.connected:
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

        results = self.manager.search("*")
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

        if not self.manager.connected:
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

        self._index_everything()

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 10)  # indexing ok

        # 2. Reset all boosts to 1
        for doc_type in settings.ZDS_APP["search"]["boosts"]:
            for key in settings.ZDS_APP["search"]["boosts"][doc_type]:
                settings.ZDS_APP["search"]["boosts"][doc_type][key] = 1.0

        # Reindex to update the weight
        self._index_everything()

        # 3. Test posts
        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        # Weights are equal without boost:
        self.assertTrue(
            response[0]["document"]["weight"] == response[1]["document"]["weight"] == response[2]["document"]["weight"]
        )

        settings.ZDS_APP["search"]["boosts"]["post"]["if_first"] = 2.0

        # Reindex to update the weights
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["weight"] == response[1]["document"]["weight"] > response[2]["document"]["weight"]
        )
        self.assertEqual(response[2]["document"]["id"], str(post_2_useful.pk))  # post 2 is the only one not first

        settings.ZDS_APP["search"]["boosts"]["post"]["if_first"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["post"]["if_useful"] = 2.0

        # Reindex to update the weights
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["weight"] > response[1]["document"]["weight"] == response[2]["document"]["weight"]
        )
        self.assertEqual(response[0]["document"]["id"], str(post_2_useful.pk))  # post 2 is useful

        settings.ZDS_APP["search"]["boosts"]["post"]["if_useful"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_above_1"] = 2.0

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["weight"] == response[1]["document"]["weight"] > response[2]["document"]["weight"]
        )
        self.assertEqual(response[0]["document"]["id"], str(post_2_useful.pk))  # post 2 have a l/d ratio of 5/2

        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_above_1"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_below_1"] = 2.0  # no one would do that in real life

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 3)

        self.assertTrue(
            response[0]["document"]["weight"] > response[1]["document"]["weight"] == response[2]["document"]["weight"]
        )
        self.assertEqual(response[0]["document"]["id"], str(post_3_ld_below_1.pk))  # post 3 have a l/d ratio of 2/5

        settings.ZDS_APP["search"]["boosts"]["post"]["ld_ratio_below_1"] = 1.0

        # Reindex to update the weight
        self._index_everything()

        # 4. Test topics
        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        # Weights are equal without boost:
        self.assertTrue(response[0]["document"]["weight"] == response[1]["document"]["weight"])

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_sticky"] = 2.0

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertTrue(response[0]["document"]["weight"] > response[1]["document"]["weight"])
        self.assertEqual(response[0]["document"]["id"], str(topic_1_solved_sticky.pk))  # topic 1 is sticky

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_sticky"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["topic"]["if_solved"] = 2.0

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertTrue(response[0]["document"]["weight"] > response[1]["document"]["weight"])
        self.assertEqual(response[0]["document"]["id"], str(topic_1_solved_sticky.pk))  # topic 1 is solved

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_solved"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["topic"]["if_locked"] = 2.0  # no one would do that in real life

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Topic.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 2)

        self.assertTrue(response[0]["document"]["weight"] > response[1]["document"]["weight"])
        self.assertEqual(response[0]["document"]["id"], str(topic_2_locked.pk))  # topic 2 is locked

        settings.ZDS_APP["search"]["boosts"]["topic"]["if_locked"] = 1.0  # no one would do that in real life

        # Reindex to update the weight
        self._index_everything()

        # 5. Test published contents
        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        # Weights are equal without boost:
        self.assertTrue(
            response[0]["document"]["weight"]
            == response[1]["document"]["weight"]
            == response[2]["document"]["weight"]
            == response[3]["document"]["weight"]
        )

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_validated"] = 2.0

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(response[0]["document"]["weight"] > response[1]["document"]["weight"])
        self.assertEqual(response[0]["document"]["id"], str(published_article.pk))  # obvious

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_validated"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_validated_and_multipage"] = 2.0

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(response[0]["document"]["weight"] > response[1]["document"]["weight"])
        self.assertEqual(response[0]["document"]["id"], str(published_tuto.pk))  # obvious

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_validated_and_multipage"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion"] = 2.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion_not_picked"] = 4.0
        # Note: in "real life", unpicked opinion would get a boost < 1.

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(
            response[0]["document"]["weight"] > response[1]["document"]["weight"] > response[2]["document"]["weight"]
        )
        self.assertEqual(
            response[0]["document"]["id"], str(published_opinion_not_picked.pk)
        )  # unpicked opinion got first
        self.assertEqual(response[1]["document"]["id"], str(published_opinion_picked.pk))

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_opinion_not_picked"] = 1.0
        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_validated_and_multipage"] = 2.0

        # Reindex to update the weight
        self._index_everything()

        result = self.client.get(reverse("search:query") + "?q=" + text + "&models=publishedcontent", follow=False)

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 5)

        self.assertTrue(response[0]["document"]["weight"] > response[1]["document"]["weight"])
        self.assertEqual(response[0]["document"]["id"], str(published_tuto.pk))  # obvious

        settings.ZDS_APP["search"]["boosts"]["publishedcontent"]["if_validated_and_multipage"] = 1.0

        # Reindex to update the weight
        self._index_everything()

        # 6. Test global boosts
        # NOTE: weights are NOT the same for all documents, no matter how hard it tries to, small differences exists

        for model in self.indexable:
            # set a huge number to overcome the small differences:
            collection = model.get_search_document_type()
            for key in settings.ZDS_APP["search"]["boosts"][collection]:
                settings.ZDS_APP["search"]["boosts"][collection][key] = 10.0

            # Reindex to update the weight
            self._index_everything()

            result = self.client.get(reverse("search:query") + "?q=" + text, follow=False)

            self.assertEqual(result.status_code, 200)
            response = result.context["object_list"]
            self.assertEqual(len(response), 10)

            self.assertEqual(response[0]["collection"], collection)  # obvious

            for key in settings.ZDS_APP["search"]["boosts"][collection]:
                settings.ZDS_APP["search"]["boosts"][collection][key] = 1

    def test_change_topic_impacts_posts(self):
        if not self.manager.connected:
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

        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 2)  # indexing ok

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 1)  # ok
        self.assertEqual(response[0]["collection"], Post.get_search_document_type())
        self.assertEqual(response[0]["document"]["forum_pk"], self.forum.pk)
        self.assertEqual(response[0]["document"]["topic_pk"], topic_1.pk)
        self.assertEqual(response[0]["document"]["topic_title"], topic_1.title)

        # 3. Change topic title and reindex
        topic_1.title = "new title"
        topic_1.save()

        self.manager.reset_index()
        self.manager.indexing_of_model(Topic, force_reindexing=True, verbose=False)
        self.manager.indexing_of_model(Post, force_reindexing=True, verbose=False)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
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

        self.manager.reset_index()
        self.manager.indexing_of_model(Topic)
        self.manager.indexing_of_model(Post)

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 1)  # Note: without staff, would not get any results (see below)

        self.assertEqual(response[0]["document"]["forum_pk"], hidden_forum.pk)  # post was updated with new forum

        # 5. Topic is now hidden
        self.client.logout()

        result = self.client.get(
            reverse("search:query") + "?q=" + text + "&models=" + Post.get_search_document_type(), follow=False
        )

        self.assertEqual(result.status_code, 200)
        response = result.context["object_list"]
        self.assertEqual(len(response), 0)  # ok

    def test_change_publishedcontents_impacts_chapter(self):
        if not self.manager.connected:
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

        results = self.manager.search("*")
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
        self.assertEqual(chapters[0]["collection"], FakeChapter.get_search_document_type())
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

        self.manager.reset_index()
        self.manager.indexing_of_model(PublishedContent, force_reindexing=True, verbose=False)
        self.manager.indexing_of_model(FakeChapter)

        results = self.manager.search("*")
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
        self.assertEqual(chapters[0]["collection"], FakeChapter.get_search_document_type())
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

        if not self.manager.connected:
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
        results = self.manager.search("*")
        number_of_results = sum(result["found"] for result in results)
        self.assertEqual(number_of_results, 0)  # indexing ok

        # index
        self._index_everything()

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

    def test_suggestion_content(self):
        text = "test"

        publishable_article1 = PublishedContentFactory(type="ARTICLE", title=f"{text} 1")
        published_article1 = PublishedContent.objects.get(content_pk=publishable_article1.pk)

        publishable_article2 = PublishedContentFactory(type="ARTICLE", title=f"{text} 2")
        published_article2 = PublishedContent.objects.get(content_pk=publishable_article2.pk)

        # Should not get a 500 if collections do not exist:
        self.manager.clear_index()
        result = self.client.get(reverse("search:suggestion") + "?q=foo", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        self._index_everything()

        # Without search term: no result
        result = self.client.get(reverse("search:suggestion"), follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # With empty query: no result
        result = self.client.get(reverse("search:suggestion") + "?q=", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # No result is returned when '*' is searched:
        result = self.client.get(reverse("search:suggestion") + "?q=*", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # Search term with zero match:
        result = self.client.get(reverse("search:suggestion") + "?q=foo", follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

        # Two matches:
        result = self.client.get(reverse("search:suggestion") + "?q=" + text, follow=False)
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 2)

        # Two matches, but they are both excluded:
        result = self.client.get(
            # /!\ This route expects IDs of publish**able** contents:
            reverse("search:suggestion") + f"?q={text}&excluded={publishable_article1.pk},{publishable_article2.pk}",
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        content = json_handler.loads(result.content.decode("utf-8"))
        self.assertEqual(len(content["results"]), 0)

    def tearDown(self):
        super().tearDown()

        # delete index:
        self.manager.clear_index()
