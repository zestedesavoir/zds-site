from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from zds.forum.commons import PostEditMixin
from zds.forum.models import Forum, Post, Topic, TopicRead
from zds.forum.tests.factories import (
    ForumCategoryFactory,
    ForumFactory,
    PostFactory,
    TagFactory,
    TopicFactory,
    create_category_and_forum,
)
from zds.forum.utils import get_tag_by_title
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.notification.models import TopicAnswerSubscription
from zds.utils import old_slugify
from zds.utils.models import Alert, Tag


class ForumMemberTests(TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        self.category1 = ForumCategoryFactory(position=1)
        self.category2 = ForumCategoryFactory(position=2)
        self.category3 = ForumCategoryFactory(position=3)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)
        self.forum13 = ForumFactory(category=self.category1, position_in_category=3)
        self.forum21 = ForumFactory(category=self.category2, position_in_category=1)
        self.forum22 = ForumFactory(category=self.category2, position_in_category=2)
        self.user = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.client.force_login(self.user)

        settings.ZDS_APP["member"]["bot_account"] = ProfileFactory().user.username

    def feed_rss_display(self):
        """Test each rss feed feed"""
        response = self.client.get(reverse("forum:post-feed-rss"), follow=False)
        self.assertEqual(response.status_code, 200)

        for forum in Forum.objects.all():
            response = self.client.get(reverse("forum:post-feed-rss") + f"?forum={forum.pk}", follow=False)
            self.assertEqual(response.status_code, 200)

        for tag in Tag.objects.all():
            response = self.client.get(reverse("forum:post-feed-rss") + f"?tag={tag.pk}", follow=False)
            self.assertEqual(response.status_code, 200)

        for forum in Forum.objects.all():
            for tag in Tag.objects.all():
                response = self.client.get(
                    reverse("forum:post-feed-rss") + f"?tag={tag.pk}&forum={forum.pk}", follow=False
                )
                self.assertEqual(response.status_code, 200)

    def test_display(self):
        """Test forum display (full: root, category, forum) Topic display test
        is in creation topic test."""
        # Forum root
        response = self.client.get(reverse("forum:cats-forums-list"))
        self.assertContains(response, "Liste des forums")
        # ForumCategory
        response = self.client.get(reverse("forum:cat-forums-list", args=[self.category1.slug]))
        self.assertContains(response, self.category1.title)
        # Forum
        response = self.client.get(reverse("forum:topics-list", args=[self.category1.slug, self.forum11.slug]))
        self.assertContains(response, self.category1.title)
        self.assertContains(response, self.forum11.title)

    def test_create_topic(self):
        """To test all aspects of topic's creation by member."""
        result = self.client.post(
            reverse("forum:topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
                "tags": "",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # check topics count
        self.assertEqual(Topic.objects.all().count(), 1)
        topic = Topic.objects.first()
        # check posts count
        self.assertEqual(Post.objects.all().count(), 1)
        post = Post.objects.first()

        # check topic and post
        self.assertEqual(post.topic, topic)
        self.assertEqual(topic.forum.pk, self.forum12.pk)

        # check position
        self.assertEqual(post.position, 1)

        self.assertEqual(post.author, self.user)
        self.assertEqual(post.editor, None)
        self.assertNotEqual(post.ip_address, None)
        self.assertNotEqual(post.text_html, None)
        self.assertEqual(post.like, 0)
        self.assertEqual(post.dislike, 0)
        self.assertEqual(post.is_visible, True)

        # check last message
        self.assertEqual(topic.last_message, post)

        # Check view
        response = self.client.get(topic.get_absolute_url())
        self.assertContains(response, self.category1.title)
        self.assertContains(response, self.forum12.title)
        self.assertContains(response, topic.title)
        self.assertContains(response, topic.subtitle)

    def test_create_topic_failing_param(self):
        """Testing different failing cases"""

        # With a weird pk
        result = self.client.post(
            reverse("forum:topic-new") + "?forum=" + "abc",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        # With a missing pk
        result = self.client.post(
            reverse("forum:topic-new") + "?forum=",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        # With a missing parameter
        result = self.client.post(
            reverse("forum:topic-new"),
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

    def test_answer(self):
        """To test all aspects of answer."""
        user1 = ProfileFactory().user
        user2 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=self.user, position=2)
        post3 = PostFactory(topic=topic1, author=user1, position=3)
        TopicRead(topic=topic1, user=user1, post=post3).save()
        TopicRead(topic=topic1, user=user2, post=post3).save()
        TopicRead(topic=topic1, user=self.user, post=post3).save()
        TopicAnswerSubscription.objects.toggle_follow(topic1, user1, True)
        TopicAnswerSubscription.objects.toggle_follow(topic1, user2, True)
        TopicAnswerSubscription.objects.toggle_follow(topic1, self.user, True)

        # check if we send an empty text
        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {"last_post": topic1.last_message.pk, "text": ""},
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        # check topics count
        self.assertEqual(Topic.objects.all().count(), 1)
        # check posts count (should be 3 for the moment)
        self.assertEqual(Post.objects.all().count(), 3)

        # now check a valid post containing utf8mb4 characters
        post_content = "Une famille 👩‍👩‍👦 mangeant un gratin d'🍆🍆 ne blesse pas les innocents 🐙🐙🐙."
        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {"last_post": topic1.last_message.pk, "text": post_content},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)

        # check topics count
        self.assertEqual(Topic.objects.all().count(), 1)

        # check posts count
        self.assertEqual(Post.objects.all().count(), 4)

        # check topic and post
        self.assertEqual(post1.topic, topic1)
        self.assertEqual(post2.topic, topic1)
        self.assertEqual(post3.topic, topic1)

        # check values
        post_final = Post.objects.last()
        self.assertEqual(post_final.topic, topic1)
        self.assertEqual(post_final.position, 4)
        self.assertEqual(post_final.editor, None)
        self.assertEqual(post_final.text, post_content)

        # test antispam return 403
        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {"last_post": topic1.last_message.pk, "text": "Testons l'antispam"},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

    def test_failing_answer_cases(self):
        """To test some failing aspects of answer."""
        user1 = ProfileFactory().user
        user2 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post3 = PostFactory(topic=topic1, author=user1, position=3)
        TopicRead(topic=topic1, user=user1, post=post3).save()
        TopicRead(topic=topic1, user=user2, post=post3).save()
        TopicRead(topic=topic1, user=self.user, post=post3).save()
        TopicAnswerSubscription.objects.toggle_follow(topic1, user1, True)
        TopicAnswerSubscription.objects.toggle_follow(topic1, user2, True)
        TopicAnswerSubscription.objects.toggle_follow(topic1, self.user, True)

        # missing parameter
        result = self.client.post(
            reverse("forum:post-new"),
            {
                "last_post": topic1.last_message.pk,
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 404)

        # weird parameter
        result = self.client.post(
            reverse("forum:post-new") + "?sujet=" + "abc",
            {
                "last_post": topic1.last_message.pk,
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 404)

        # non-existing (yet) parameter
        result = self.client.post(
            reverse("forum:post-new") + "?sujet=" + "424242",
            {
                "last_post": topic1.last_message.pk,
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 404)

    def test_edit_main_post(self):
        """To test all aspects of the edition of main post by member."""
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        topic2 = TopicFactory(forum=self.forum12, author=self.user)
        post2 = PostFactory(topic=topic2, author=self.user, position=1)
        topic3 = TopicFactory(forum=self.forum21, author=self.user)
        post3 = PostFactory(topic=topic3, author=self.user, position=1)

        expected_title = "Un autre sujet"
        expected_subtitle = "Encore ces lombards en plein été"
        expected_text = "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter "
        result = self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic1.pk}",
            {"title": expected_title, "subtitle": expected_subtitle, "text": expected_text, "tags": ""},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

        # check topics count
        self.assertEqual(Topic.objects.all().count(), 3)

        # check posts count
        self.assertEqual(Post.objects.all().count(), 3)

        # check topic and post
        self.assertEqual(post1.topic, topic1)
        self.assertEqual(post2.topic, topic2)
        self.assertEqual(post3.topic, topic3)

        # check values
        self.assertEqual(expected_title, Topic.objects.get(pk=topic1.pk).title)
        self.assertEqual(expected_subtitle, Topic.objects.get(pk=topic1.pk).subtitle)
        self.assertEqual(expected_text, Post.objects.get(pk=post1.pk).text)

        # check edit data
        self.assertEqual(Post.objects.get(pk=post1.pk).editor, self.user)

        # check if topic is valid (no topic)
        result = self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic2.pk}",
            {"title": "", "subtitle": expected_subtitle, "text": expected_text, "tags": ""},
            follow=False,
        )
        self.assertEqual(Topic.objects.get(pk=topic2.pk).title, topic2.title)

        # check if topic is valid (tags only)
        result = self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic2.pk}",
            {"title": "", "subtitle": expected_subtitle, "text": expected_text, "tags": "foo, bar"},
            follow=False,
        )
        self.assertEqual(Topic.objects.get(pk=topic2.pk).title, topic2.title)

        # check if topic is valid (spaces only)
        result = self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic2.pk}",
            {"title": "  ", "subtitle": expected_subtitle, "text": expected_text, "tags": ""},
            follow=False,
        )
        self.assertEqual(Topic.objects.get(pk=topic2.pk).title, topic2.title)

        # check if topic is valid (valid title)
        result = self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic2.pk}",
            {"title": expected_title, "subtitle": expected_subtitle, "text": expected_text, "tags": ""},
            follow=False,
        )
        self.assertEqual(expected_title, Topic.objects.get(pk=topic2.pk).title)

    def test_edit_post(self):
        """To test all aspects of the edition of simple post by member."""
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=self.user, position=2)
        post3 = PostFactory(topic=topic1, author=self.user, position=3)

        result = self.client.post(
            reverse("forum:post-edit") + f"?message={post2.pk}",
            {"text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter "},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

        # check topics count
        self.assertEqual(Topic.objects.all().count(), 1)

        # check posts count
        self.assertEqual(Post.objects.all().count(), 3)

        # check topic and post
        self.assertEqual(post1.topic, topic1)
        self.assertEqual(post2.topic, topic1)
        self.assertEqual(post3.topic, topic1)

        # check values
        self.assertEqual(
            Post.objects.get(pk=post2.pk).text,
            "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
        )

        # check edit data
        self.assertEqual(Post.objects.get(pk=post2.pk).editor, self.user)

        # if the post pk is altered
        result = self.client.post(
            reverse("forum:post-edit") + "?message=abcd",
            {"text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter "},
            follow=False,
        )

        self.assertEqual(result.status_code, 404)

    def test_edit_post_with_blank(self):
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=self.user, position=2)
        post3 = PostFactory(topic=topic1, author=self.user, position=3)

        result = self.client.post(reverse("forum:post-edit") + f"?message={post2.pk}", {"text": "  "}, follow=True)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.request["PATH_INFO"], "/forums/message/modifier/")
        self.assertEqual(result.request["QUERY_STRING"], f"message={post2.pk}")

        result = self.client.post(
            reverse("forum:post-edit") + f"?message={post3.pk}", {"text": " contenu "}, follow=True
        )

        self.assertEqual(result.status_code, 200)
        self.assertNotEqual(result.request["PATH_INFO"], "/forums/message/editer/")

    def test_quote_post(self):
        """To test when a member quote anyone post."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.get(reverse("forum:post-new") + f"?sujet={topic1.pk}&cite={post2.pk}", follow=True)

        self.assertEqual(result.status_code, 200)

        # if the quote pk is altered
        result = self.client.get(reverse("forum:post-new") + f"?sujet={topic1.pk}&cite=abcd", follow=True)

        self.assertEqual(result.status_code, 404)

    def test_signal_post(self):
        """To test when a member signals a post."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.post(
            reverse("forum:post-create-alert") + f"?message={post2.pk}",
            {"signal_text": "Troll", "signal_message": "confirmer"},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.filter(solved=False).count(), 1)
        self.assertEqual(Alert.objects.filter(author=self.user, solved=False).count(), 1)
        self.assertEqual(Alert.objects.get(author=self.user, solved=False).text, "Troll")

        result = self.client.post(
            reverse("forum:post-create-alert") + f"?message={post1.pk}",
            {"signal_text": "Bad title", "signal_message": "confirmer"},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.filter(solved=False).count(), 2)
        self.assertEqual(Alert.objects.filter(author=self.user, solved=False).count(), 2)
        self.assertEqual(list(Alert.objects.filter(author=self.user, solved=False))[1].text, "Bad title")

        # and test that staff can solve but not user
        alert = Alert.objects.get(comment=post2.pk)
        # try as a normal user
        result = self.client.post(
            reverse("forum:solve-alert"),
            {
                "alert_pk": alert.pk,
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 403)
        # login as staff
        staff1 = StaffProfileFactory().user
        self.client.force_login(staff1)
        # try again as staff
        resolve_reason = "Everything is OK kid"
        result = self.client.post(
            reverse("forum:solve-alert"), {"alert_pk": alert.pk, "text": resolve_reason}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        alert = Alert.objects.get(pk=alert.pk)
        self.assertEqual(alert.resolve_reason, resolve_reason)
        self.assertTrue(alert.solved)
        self.assertEqual(Alert.objects.filter(author=self.user, solved=False).count(), 1)
        self.assertEqual(Alert.objects.filter(author=self.user, solved=True).count(), 1)

        # staff hides a message
        data = {
            "delete_message": "",
            "text_hidden": "Bad guy!",
        }
        response = self.client.post(reverse("forum:post-edit") + f"?message={post1.pk}", data, follow=False)
        self.assertEqual(302, response.status_code)
        # alerts automatically solved
        self.assertEqual(Alert.objects.filter(author=self.user, solved=False).count(), 0)
        self.assertEqual(Alert.objects.filter(author=self.user, solved=True).count(), 2)

    def test_signal_and_solve_alert_empty_message(self):
        """To test when a member signal a post and staff solve it."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.post(
            reverse("forum:post-create-alert") + f"?message={post2.pk}",
            {"signal_text": "Troll", "signal_message": "confirmer"},
            follow=False,
        )

        alert = Alert.objects.get(comment=post2.pk)
        # login as staff
        staff1 = StaffProfileFactory().user
        self.client.force_login(staff1)
        # try again as staff
        result = self.client.post(
            reverse("forum:solve-alert"),
            {
                "alert_pk": alert.pk,
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.filter(solved=False).count(), 0)

    def test_useful_post(self):
        """To test when a member mark a post is usefull."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        post3 = PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.post(reverse("forum:post-useful") + f"?message={post2.pk}", follow=False)

        self.assertEqual(result.status_code, 302)

        self.assertEqual(Post.objects.get(pk=post1.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post2.pk).is_useful, True)
        self.assertEqual(Post.objects.get(pk=post3.pk).is_useful, False)

        # useful the first post
        result = self.client.post(reverse("forum:post-useful") + f"?message={post1.pk}", follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Post.objects.get(pk=post1.pk).is_useful, True)
        self.assertEqual(Post.objects.get(pk=post2.pk).is_useful, True)
        self.assertEqual(Post.objects.get(pk=post3.pk).is_useful, False)

        # useful if you aren't author
        TopicFactory(forum=self.forum11, author=user1)
        post4 = PostFactory(topic=topic1, author=user1, position=1)
        post5 = PostFactory(topic=topic1, author=self.user, position=2)

        result = self.client.post(reverse("forum:post-useful") + f"?message={post5.pk}", follow=False)

        self.assertEqual(result.status_code, 302)

        self.assertEqual(Post.objects.get(pk=post4.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post5.pk).is_useful, True)

        # useful if you are staff
        staff = StaffProfileFactory().user
        self.client.force_login(staff)
        result = self.client.post(reverse("forum:post-useful") + f"?message={post4.pk}", follow=False)
        self.assertNotEqual(result.status_code, 403)
        self.assertEqual(Post.objects.get(pk=post4.pk).is_useful, True)
        self.assertEqual(Post.objects.get(pk=post5.pk).is_useful, True)

    def test_failing_useful_post(self):
        """To test some failing cases when a member mark a post is useful."""

        # missing parameter
        result = self.client.post(reverse("forum:post-useful"), follow=False)

        self.assertEqual(result.status_code, 404)

        # weird parameter
        result = self.client.post(reverse("forum:post-useful") + "?message=" + "abc", follow=False)

        self.assertEqual(result.status_code, 404)

        # not existing (yet) pk parameter
        result = self.client.post(reverse("forum:post-useful") + "?message=" + "424242", follow=False)

        self.assertEqual(result.status_code, 404)

    def test_move_topic(self):
        """Test topic move."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        # not staff member can't move topic
        result = self.client.post(
            reverse("forum:topic-edit"), {"move": "", "forum": self.forum12, "topic": topic1.pk}, follow=False
        )

        self.assertEqual(result.status_code, 403)

        # test with staff
        staff1 = StaffProfileFactory().user
        self.client.force_login(staff1)

        result = self.client.post(
            reverse("forum:topic-edit"), {"move": "", "forum": self.forum12.pk, "topic": topic1.pk}, follow=False
        )

        self.assertEqual(result.status_code, 302)

        # check value
        self.assertEqual(Topic.objects.get(pk=topic1.pk).forum.pk, self.forum12.pk)

    def test_failing_moving_topic(self):
        """Test some failing case when playing with the "move topic" feature"""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        # log as staff
        staff1 = StaffProfileFactory().user
        self.client.force_login(staff1)

        # missing parameter
        result = self.client.post(
            reverse("forum:topic-edit"),
            {
                "move": "",
                "forum": self.forum12.pk,
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 404)

        # weird parameter
        result = self.client.post(
            reverse("forum:topic-edit"), {"move": "", "forum": self.forum12.pk, "topic": "abc"}, follow=False
        )

        self.assertEqual(result.status_code, 404)

        # non-existing (yet) parameter
        result = self.client.post(
            reverse("forum:topic-edit"), {"move": "", "forum": self.forum12.pk, "topic": "424242"}, follow=False
        )

        self.assertEqual(result.status_code, 404)

    def test_answer_empty(self):
        """Test behaviour on empty answer."""
        # Topic and 1st post by another user, to avoid antispam limitation
        topic1 = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic1, author=self.user2, position=1)

        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {"last_post": topic1.last_message.pk, "text": " "},
            follow=False,
        )

        # Empty text --> preview = HTTP 200 + post not saved (only 1 post in
        # topic)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(Post.objects.filter(topic=topic1.pk).count(), 1)

    def test_add_tag(self):
        tag_c_sharp = TagFactory(title="C#")

        tag_c = TagFactory(title="C")
        self.assertNotEqual(tag_c_sharp.slug, tag_c.slug)  # uniqueness of the slug!
        self.assertNotEqual(tag_c_sharp.title, tag_c.title)
        # post a topic with a tag
        result = self.client.post(
            reverse("forum:topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
                "tags": "C#",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # test the topic is added to the good tag
        self.assertEqual(
            Topic.objects.filter(tags__in=[tag_c_sharp])
            .order_by("-last_message__pubdate")
            .prefetch_related("tags")
            .count(),
            1,
        )
        self.assertEqual(
            Topic.objects.filter(tags__in=[tag_c]).order_by("-last_message__pubdate").prefetch_related("tags").count(),
            0,
        )

        topic_with_conflict_tags = TopicFactory(forum=self.forum11, author=self.user)
        topic_with_conflict_tags.title = "[C][c][ c][C ]name"
        (tags, title) = get_tag_by_title(topic_with_conflict_tags.title)
        topic_with_conflict_tags.add_tags(tags)
        self.assertEqual(topic_with_conflict_tags.tags.all().count(), 1)

        topic_with_conflict_tags = TopicFactory(forum=self.forum11, author=self.user)
        topic_with_conflict_tags.title = "[][ ][   ]name"
        (tags, title) = get_tag_by_title(topic_with_conflict_tags.title)
        topic_with_conflict_tags.add_tags(tags)
        self.assertEqual(topic_with_conflict_tags.tags.all().count(), 0)

        topic_with_utf8mb4_tags = TopicFactory(forum=self.forum11, author=self.user)
        topic_with_utf8mb4_tags.title = "[🍆][tag987][🐙]name"
        (tags, title) = get_tag_by_title(topic_with_utf8mb4_tags.title)
        topic_with_utf8mb4_tags.add_tags(tags)
        self.assertEqual(topic_with_utf8mb4_tags.tags.all().count(), 1)

    def test_mandatory_fields_on_new(self):
        """Test handeling of mandatory fields on new topic creation."""
        init_topic_count = Topic.objects.all().count()

        # Empty fields
        response = self.client.post(reverse("forum:topic-new") + f"?forum={self.forum12.pk}", {}, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.all().count(), init_topic_count)

        # Blank data
        response = self.client.post(
            reverse("forum:topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": " ",
                "text": " ",
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.all().count(), init_topic_count)

    def test_url_topic(self):
        """Test simple get request to the topic."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        # simple member can read public topic
        result = self.client.get(
            reverse("forum:topic-posts-list", args=[topic1.pk, old_slugify(topic1.title)]), follow=True
        )
        self.assertEqual(result.status_code, 200)

    def test_failing_unread_post(self):
        """Test failing cases when a member try to mark as unread a post."""

        # parameter is missing
        result = self.client.get(reverse("forum:post-unread"), follow=False)

        self.assertEqual(result.status_code, 404)

        # parameter is weird
        result = self.client.get(reverse("forum:post-unread") + "?message=" + "abc", follow=False)

        self.assertEqual(result.status_code, 404)

        # pk doesn't (yet) exist
        result = self.client.get(reverse("forum:post-unread") + "?message=" + "424242", follow=False)

        self.assertEqual(result.status_code, 404)

    def test_frontend_alert_existence_other_pages(self):
        forum = self.forum11
        profiles = [ProfileFactory(), ProfileFactory()]
        topic = TopicFactory(forum=forum, author=profiles[1].user)
        expected = "<strong>Attention</strong>, vous n’êtes pas sur la dernière page de "
        expected += "ce sujet. Assurez-vous de l’avoir lu dans son intégralité avant d’y"
        expected += " répondre."

        for i in range(settings.ZDS_APP["forum"]["posts_per_page"] + 2):
            PostFactory(topic=topic, author=profiles[i % 2].user, position=i + 2)
        self.client.force_login(profiles[1].user)

        template_response = self.client.get(topic.get_absolute_url())
        self.assertIn(expected, template_response.content.decode("utf-8"))

        template_response = self.client.get(topic.get_absolute_url() + "?page=2")
        self.assertNotIn(expected, template_response.content.decode("utf-8"))

    def test_frontend_topic_message_when_profile_readonly(self):
        readonly_profile = ProfileFactory(can_write=False)
        self.client.force_login(readonly_profile.user)

        topic = TopicFactory(forum=self.forum11, author=readonly_profile.user)
        PostFactory(topic=topic, author=readonly_profile.user, position=1)
        PostFactory(topic=topic, author=self.user, position=2)

        template_response = self.client.get(topic.get_absolute_url())
        decoded_content = template_response.content.decode("utf-8")
        self.assertNotIn("Nouveau sujet", decoded_content)
        self.assertNotIn("Éditer le sujet", decoded_content)
        self.assertIn("Vous êtes en lecture seule. Vous ne pouvez pas poster de messages.", decoded_content)

    def test_frontend_topic_no_message_when_profile_can_write(self):
        self.client.force_login(self.user2)

        topic = TopicFactory(forum=self.forum11, author=self.user2)
        PostFactory(topic=topic, author=self.user2, position=1)
        PostFactory(topic=topic, author=self.user, position=2)

        template_response = self.client.get(topic.get_absolute_url())
        decoded_content = template_response.content.decode("utf-8")
        self.assertIn("Nouveau sujet", decoded_content)
        self.assertIn("Éditer le sujet", decoded_content)
        self.assertNotIn("Vous êtes en lecture seule. Vous ne pouvez pas poster de messages.", decoded_content)

    def test_frontend_no_create_topic_when_profile_readonly(self):
        readonly_profile = ProfileFactory(can_write=False)
        self.client.force_login(readonly_profile.user)

        template_response = self.client.get(self.forum22.get_absolute_url())
        self.assertNotIn("Nouveau sujet", template_response.content.decode("utf-8"))

    def test_frontend_can_create_topic_when_profile_can_write(self):
        self.client.force_login(self.user)
        template_response = self.client.get(self.forum22.get_absolute_url())
        self.assertIn("Nouveau sujet", template_response.content.decode("utf-8"))


class ForumGuestTests(TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        self.category1 = ForumCategoryFactory(position=1)
        self.category2 = ForumCategoryFactory(position=2)
        self.category3 = ForumCategoryFactory(position=3)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)
        self.forum13 = ForumFactory(category=self.category1, position_in_category=3)
        self.forum21 = ForumFactory(category=self.category2, position_in_category=1)
        self.forum22 = ForumFactory(category=self.category2, position_in_category=2)
        self.user = ProfileFactory().user

    def feed_rss_display(self):
        """Test each rss feed feed"""
        response = self.client.get(reverse("forum:post-feed-rss"), follow=False)
        self.assertEqual(response.status_code, 200)

        for forum in Forum.objects.all():
            response = self.client.get(reverse("forum:post-feed-rss") + f"?forum={forum.pk}", follow=False)
            self.assertEqual(response.status_code, 200)

        for tag in Tag.objects.all():
            response = self.client.get(reverse("forum:post-feed-rss") + f"?tag={tag.pk}", follow=False)
            self.assertEqual(response.status_code, 200)

        for forum in Forum.objects.all():
            for tag in Tag.objects.all():
                response = self.client.get(
                    reverse("forum:post-feed-rss") + f"?tag={tag.pk}&forum={forum.pk}", follow=False
                )
                self.assertEqual(response.status_code, 200)

    def test_display(self):
        """Test forum display (full: root, category, forum) Topic display test
        is in creation topic test."""
        # Forum root
        response = self.client.get(reverse("forum:cats-forums-list"))
        self.assertContains(response, "Liste des forums")
        # ForumCategory
        response = self.client.get(reverse("forum:cat-forums-list", args=[self.category1.slug]))
        self.assertContains(response, self.category1.title)
        # Forum
        response = self.client.get(reverse("forum:topics-list", args=[self.category1.slug, self.forum11.slug]))
        self.assertContains(response, self.category1.title)
        self.assertContains(response, self.forum11.title)

    def test_create_topic(self):
        """To test all aspects of topic's creation by guest."""
        result = self.client.post(
            reverse("forum:topic-new") + f"?forum={self.forum12.pk}",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein ete",
                "text": "C'est tout simplement l'histoire de " "la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # check topics count
        self.assertEqual(Topic.objects.all().count(), 0)
        # check posts count
        self.assertEqual(Post.objects.all().count(), 0)

    def test_answer(self):
        """To test all aspects of answer."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=self.user, position=2)
        PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic1.pk}",
            {
                "last_post": topic1.last_message.pk,
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

        # check topics count
        self.assertEqual(Topic.objects.all().count(), 1)

        # check posts count
        self.assertEqual(Post.objects.all().count(), 3)

    def test_edit_main_post(self):
        """To test all aspects of the edition of main post by guest."""
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        topic2 = TopicFactory(forum=self.forum12, author=self.user)
        PostFactory(topic=topic2, author=self.user, position=1)
        topic3 = TopicFactory(forum=self.forum21, author=self.user)
        PostFactory(topic=topic3, author=self.user, position=1)

        result = self.client.post(
            reverse("forum:post-edit") + f"?message={post1.pk}",
            {
                "title": "Un autre sujet",
                "subtitle": "Encore ces lombards en plein été",
                "text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter ",
            },
            follow=False,
        )

        self.assertEqual(result.status_code, 302)

        self.assertNotEqual(Topic.objects.get(pk=topic1.pk).title, "Un autre sujet")
        self.assertNotEqual(Topic.objects.get(pk=topic1.pk).subtitle, "Encore ces lombards en plein été")
        self.assertNotEqual(
            Post.objects.get(pk=post1.pk).text,
            "C'est tout simplement l'histoire de la ville de " "Paris que je voudrais vous conter ",
        )

    def test_edit_post(self):
        """To test all aspects of the edition of simple post by guest."""
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=self.user, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        result = self.client.post(
            reverse("forum:post-edit") + f"?message={post2.pk}",
            {"text": "C'est tout simplement l'histoire de la ville de Paris que je voudrais vous conter "},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)
        self.assertNotEqual(
            Post.objects.get(pk=post2.pk).text,
            "C'est tout simplement l'histoire de la ville de " "Paris que je voudrais vous conter ",
        )

    def test_quote_post(self):
        """To test when a member quote anyone post."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.get(reverse("forum:post-new") + f"?sujet={topic1.pk}&cite={post2.pk}", follow=False)

        self.assertEqual(result.status_code, 302)

    def test_signal_post(self):
        """To test when a member quote anyone post."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.post(
            reverse("forum:post-edit") + f"?message={post2.pk}",
            {"signal_text": "Troll", "signal_message": "confirmer"},
            follow=False,
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.filter(solved=False).count(), 0)
        self.assertEqual(Alert.objects.filter(author=self.user, solved=False).count(), 0)

    def test_useful_post(self):
        """To test when a guest mark a post is usefull."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position=1)
        post2 = PostFactory(topic=topic1, author=user1, position=2)
        post3 = PostFactory(topic=topic1, author=user1, position=3)

        result = self.client.get(reverse("forum:post-useful") + f"?message={post2.pk}", follow=False)

        self.assertEqual(result.status_code, 405)

        self.assertEqual(Post.objects.get(pk=post1.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post2.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post3.pk).is_useful, False)

    def test_move_topic(self):
        """Test topic move."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        # not staff guest can't move topic
        result = self.client.post(
            reverse("forum:topic-edit"), {"move": "", "forum": self.forum12, "topic": topic1.pk}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertNotEqual(Topic.objects.get(pk=topic1.pk).forum, self.forum12)

    def test_url_topic(self):
        """Test simple get request to the topic."""
        user1 = ProfileFactory().user
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        # guest can read public topic
        result = self.client.get(
            reverse("forum:topic-posts-list", args=[topic1.pk, old_slugify(topic1.title)]), follow=True
        )
        self.assertEqual(result.status_code, 200)

    def test_filter_topic(self):
        """Test filters for topics"""

        ProfileFactory().user

        topic = TopicFactory(forum=self.forum11, author=self.user, is_sticky=False)
        PostFactory(topic=topic, author=self.user, position=1)

        topic_solved = TopicFactory(forum=self.forum11, author=self.user, solved_by=self.user, is_sticky=False)
        PostFactory(topic=topic_solved, author=self.user, position=1)

        topic_sticky = TopicFactory(forum=self.forum11, author=self.user, is_sticky=True)
        PostFactory(topic=topic_sticky, author=self.user, position=1)

        topic_solved_sticky = TopicFactory(forum=self.forum11, author=self.user, solved_by=self.user, is_sticky=True)
        PostFactory(topic=topic_solved_sticky, author=self.user, position=1)

        # no filter

        # all normal (== not sticky) topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=False)), 2)
        self.assertIn(topic_solved, get_topics(forum_pk=self.forum11.pk, is_sticky=False))
        self.assertIn(topic, get_topics(forum_pk=self.forum11.pk, is_sticky=False))

        # all sticky topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=True)), 2)
        self.assertIn(topic_solved_sticky, get_topics(forum_pk=self.forum11.pk, is_sticky=True))

        # solved filter

        # solved topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=False, filter="solve")), 1)
        self.assertEqual(get_topics(forum_pk=self.forum11.pk, is_sticky=False, filter="solve")[0], topic_solved)

        # solved sticky topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=True, filter="solve")), 1)
        self.assertEqual(get_topics(forum_pk=self.forum11.pk, is_sticky=True, filter="solve")[0], topic_solved_sticky)

        # unsolved filter

        # unsolved topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=False, filter="unsolve")), 1)
        self.assertEqual(get_topics(forum_pk=self.forum11.pk, is_sticky=False, filter="unsolve")[0], topic)

        # unsolved sticky topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=True, filter="unsolve")), 1)
        self.assertEqual(get_topics(forum_pk=self.forum11.pk, is_sticky=True, filter="unsolve")[0], topic_sticky)

        # no answer filter

        user1 = ProfileFactory().user

        # create a new topic with answers
        topic1 = TopicFactory(forum=self.forum11, author=self.user, is_sticky=False)
        PostFactory(topic=topic1, author=self.user, position=1)
        PostFactory(topic=topic1, author=user1, position=2)
        PostFactory(topic=topic1, author=self.user, position=3)

        # create a new sticky topic with answers
        topic2 = TopicFactory(forum=self.forum11, author=self.user, is_sticky=True)
        PostFactory(topic=topic2, author=self.user, position=1)
        PostFactory(topic=topic2, author=user1, position=2)
        PostFactory(topic=topic2, author=self.user, position=3)

        # all normal (== not sticky) topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=False)), 3)  # 2 normal + 1 with answers
        self.assertIn(topic1, get_topics(forum_pk=self.forum11.pk, is_sticky=False))

        # all sticky topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=True)), 3)  # 2 normal + 1 with answers
        self.assertIn(topic2, get_topics(forum_pk=self.forum11.pk, is_sticky=True))

        # no answer topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=False, filter="noanswer")), 2)
        self.assertIn(topic_solved, get_topics(forum_pk=self.forum11.pk, is_sticky=False, filter="noanswer"))

        # no answer sticky topics
        self.assertEqual(len(get_topics(forum_pk=self.forum11.pk, is_sticky=True, filter="noanswer")), 2)
        self.assertIn(
            topic_solved_sticky,
            get_topics(forum_pk=self.forum11.pk, is_sticky=True, filter="noanswer"),
        )

    def test_old_post_limit(self):
        topic = TopicFactory(forum=self.forum11, author=self.user, is_sticky=False)

        # Create a post published just now
        PostFactory(topic=topic, author=self.user, position=1)
        self.assertEqual(topic.old_post_warning(), False)

        # Create a post published one day before old_post_limit_days
        old_post = PostFactory(topic=topic, author=self.user, position=2)
        old_post.pubdate = datetime.now() - timedelta(days=(settings.ZDS_APP["forum"]["old_post_limit_days"] + 1))
        old_post.save()
        self.assertEqual(topic.old_post_warning(), True)


def get_topics(forum_pk, is_sticky, filter=None):
    """
    Get topics for a forum.
    The optional filter allows to retrieve only solved, unsolved or "non-answered" (i.e. with only the 1st post) topics.
    :param forum_pk: the primary key of forum
    :param is_sticky: indicates if the sticky topics must or must not be retrieved
    :param filter: optional filter to retrieve only specific topics.
    :return:
    """

    if filter == "solve":
        topics = Topic.objects.filter(forum__pk=forum_pk, is_sticky=is_sticky, solved_by__isnull=False)
    elif filter == "unsolve":
        topics = Topic.objects.filter(forum__pk=forum_pk, is_sticky=is_sticky, solved_by__isnull=True)
    elif filter == "noanswer":
        topics = Topic.objects.filter(forum__pk=forum_pk, is_sticky=is_sticky, last_message__position=1)
    else:
        topics = Topic.objects.filter(forum__pk=forum_pk, is_sticky=is_sticky)

    return (
        topics.order_by("-last_message__pubdate")
        .select_related("author__profile")
        .prefetch_related("last_message", "tags")
        .all()
    )


class ManagerTests(TestCase):
    def setUp(self):
        self.cat1 = ForumCategoryFactory()
        self.forum1 = ForumFactory(category=self.cat1)
        self.forum2 = ForumFactory(category=self.cat1)

        self.staff = StaffProfileFactory()
        staff_group = Group.objects.filter(name="staff").first()

        self.forum3 = ForumFactory(category=self.cat1)
        self.forum3.groups.add(staff_group)
        self.forum3.save()

        TopicFactory(forum=self.forum1, author=self.staff.user)
        TopicFactory(forum=self.forum2, author=self.staff.user)
        TopicFactory(forum=self.forum3, author=self.staff.user)

    def test_get_last_topics(self):
        topics = Topic.objects.get_last_topics()
        self.assertEqual(2, len(topics))

    def test_get_unread_post(self):
        author = ProfileFactory()
        topic = TopicFactory(author=author.user, forum=self.forum1)
        post = PostFactory(topic=topic, position=1, author=author.user)
        topic.last_post = post
        topic.save()
        TopicRead(user=author.user, post=post, topic=topic).save()
        topic.last_post = PostFactory(author=self.staff.user, topic=topic, position=2)
        topic.save()
        TopicRead(post=topic.last_post, user=self.staff.user, topic=topic).save()
        self.assertEqual(1, len(TopicRead.objects.list_read_topic_pk(self.staff.user)))
        self.assertEqual(0, len(TopicRead.objects.list_read_topic_pk(author.user)))

    def test_is_read(self):
        author = ProfileFactory()
        reader = ProfileFactory()
        topic: Topic = TopicFactory(author=author.user, forum=self.forum1)
        post = PostFactory(topic=topic, position=1, author=author.user)
        topic.last_post = post
        topic.save()
        TopicRead(post=topic.last_post, user=self.staff.user, topic=topic).save()
        self.assertFalse(Topic.objects.get(pk=topic.pk).is_read)
        self.assertFalse(topic.is_read_by_user(author.user, check_auth=False))
        self.assertTrue(topic.is_read_by_user(self.staff.user, check_auth=False))
        self.assertFalse(topic.is_read_by_user(reader.user, check_auth=False))

    def test_get_authorized_forums_pk(self):
        user = ProfileFactory().user
        hidden_forum = self.forum3

        # Regular user can access only the public forum:
        self.assertEqual(sorted(Forum.objects.get_authorized_forums_pk(user)), sorted([self.forum1.pk, self.forum2.pk]))

        # Staff user can access all forums:
        self.assertEqual(
            sorted(Forum.objects.get_authorized_forums_pk(self.staff.user)),
            sorted([self.forum1.pk, self.forum2.pk, hidden_forum.pk]),
        )

        # By default, only public forums are available:
        self.assertEqual(sorted(Forum.objects.get_authorized_forums_pk(None)), sorted([self.forum1.pk, self.forum2.pk]))


class TopicReadAndUnreadTests(TestCase):
    def setUp(self):
        self.author = ProfileFactory().user
        self.reader = ProfileFactory().user
        self.topic = TopicFactory(
            author=self.author, forum=ForumFactory(category=ForumCategoryFactory(), position_in_category=1)
        )

    def test_first_unread_on_non_read_op(self):
        post = PostFactory(topic=self.topic, author=self.author, position=1)
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(post, topic.first_unread_post(self.reader))

    def test_first_unread_on_read_op(self):
        post = PostFactory(topic=self.topic, author=self.author, position=1)
        TopicRead(topic=self.topic, post=post, user=self.reader).save()
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(None, topic.first_unread_post(self.reader))

    def test_first_unread_on_read_other_message(self):
        op = PostFactory(topic=self.topic, author=self.author, position=1)
        TopicRead(topic=self.topic, post=op, user=self.reader).save()
        post = PostFactory(topic=self.topic, author=ProfileFactory().user, position=2)
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(post, topic.first_unread_post(self.reader))

    def test_first_unread_on_not_read_other_message(self):
        op = PostFactory(topic=self.topic, author=self.author, position=1)
        PostFactory(topic=self.topic, author=ProfileFactory().user, position=2)
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(op, topic.first_unread_post(self.reader))

    def test_two_messages_read(self):
        op = PostFactory(topic=self.topic, author=self.author, position=1)
        TopicRead(topic=self.topic, post=op, user=self.reader).save()
        post = PostFactory(topic=self.topic, author=ProfileFactory().user, position=2)
        PostFactory(topic=self.topic, author=ProfileFactory().user, position=3)
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(post, topic.first_unread_post(self.reader))


class TestMixins(TestCase):
    def test_double_unread_is_handled(self):
        author = ProfileFactory().user
        viewer = ProfileFactory().user
        topic = TopicFactory(author=author, forum=ForumFactory(category=ForumCategoryFactory(), position_in_category=1))
        post = PostFactory(topic=topic, author=author, position=1)
        TopicRead(topic=topic, post=post, user=viewer).save()
        PostEditMixin.perform_unread_message(post, viewer)
        PostEditMixin.perform_unread_message(post, viewer)
        self.assertEqual(0, TopicRead.objects.count())
