from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Post, Topic
from zds.forum.tests.factories import PostFactory, TagFactory, create_category_and_forum, create_topic_in_forum
from zds.member.tests.factories import DevProfileFactory, ProfileFactory, StaffProfileFactory
from zds.notification.models import TopicAnswerSubscription
from zds.utils.models import CommentEdit, Hat


class LastTopicsViewTests(TestCase):
    def test_logged_user(self):
        profile = ProfileFactory()
        self.client.force_login(profile.user)
        _, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile)
        response = self.client.get(reverse("forum:last-subjects"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(Topic.objects.last() in response.context["topics"])

    def test_anonymous_user(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile)
        response = self.client.get(reverse("forum:last-subjects"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(Topic.objects.last() in response.context["topics"])

    def test_private_topic(self):
        author_profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        _, forum = create_category_and_forum(group)
        create_topic_in_forum(forum, author_profile)
        # Tests with a user who cannot read the last topic.
        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:last-subjects"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(Topic.objects.last() not in response.context["topics"])
        # Adds to the user the right to read the last topic, and test again.
        profile.user.groups.add(group)
        profile.user.save()
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:last-subjects"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(Topic.objects.last() in response.context["topics"])


class CategoriesForumsListViewTests(TestCase):
    def test_success_list_all_forums(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()

        response = self.client.get(reverse("forum:cats-forums-list"))

        self.assertEqual(200, response.status_code)
        current_category = response.context["categories"].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])

    def test_success_list_all_forums_with_private_forums(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category, forum = create_category_and_forum(group)

        response = self.client.get(reverse("forum:cats-forums-list"))

        self.assertEqual(200, response.status_code)
        current_category = response.context["categories"].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(0, len(current_category.get_forums(profile.user)))

        profile.user.groups.add(group)
        profile.user.save()
        self.client.force_login(profile.user)

        response = self.client.get(reverse("forum:cats-forums-list"))

        self.assertEqual(200, response.status_code)
        current_category = response.context["categories"].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])

    def test_topic_list_home_page(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        topics_nb = len(Topic.objects.get_last_topics())

        self.client.force_login(staff.user)
        data = {"lock": "true", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_locked)

        self.assertEqual(len(Topic.objects.get_last_topics()), topics_nb - 1)


class CategoryForumsDetailViewTest(TestCase):
    def test_success_list_all_forums_of_a_category(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()

        response = self.client.get(reverse("forum:cat-forums-list", args=[category.slug]))

        self.assertEqual(200, response.status_code)
        current_category = response.context["category"]
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])
        self.assertEqual(response.context["forums"][0], current_category.get_forums(profile.user)[0])

    def test_success_list_all_forums_of_a_category_with_private_forums(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category, forum = create_category_and_forum(group)

        response = self.client.get(reverse("forum:cat-forums-list", args=[category.slug]))

        self.assertEqual(200, response.status_code)
        current_category = response.context["category"]
        self.assertEqual(category, current_category)
        self.assertEqual(0, len(response.context["forums"]))

        profile.user.groups.add(group)
        profile.user.save()
        self.client.force_login(profile.user)

        response = self.client.get(reverse("forum:cat-forums-list", args=[category.slug]))

        self.assertEqual(200, response.status_code)
        current_category = response.context["category"]
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])
        self.assertEqual(response.context["forums"][0], current_category.get_forums(profile.user)[0])


class ForumTopicsListViewTest(TestCase):
    def test_failure_list_all_topics_of_a_wrong_forum(self):
        response = self.client.get(reverse("forum:topics-list", args=["x", "x"]))

        self.assertEqual(404, response.status_code)

    def test_failure_list_all_topics_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")
        category, forum = create_category_and_forum(group)

        response = self.client.get(reverse("forum:topics-list", args=[category.slug, forum.slug]))

        self.assertEqual(403, response.status_code)

    def test_success_list_all_topics_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:topics-list", args=[category.slug, forum.slug]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context["forum"])
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])
        self.assertEqual(0, len(response.context["sticky_topics"]))

    def test_success_list_all_topics_of_a_forum_with_sticky_topics(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        topic_sticky = create_topic_in_forum(forum, profile, is_sticky=True)

        response = self.client.get(reverse("forum:topics-list", args=[category.slug, forum.slug]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context["forum"])
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])
        self.assertEqual(1, len(response.context["sticky_topics"]))
        self.assertEqual(topic_sticky, response.context["sticky_topics"][0])

    def test_success_filter_list_all_topics_solved_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile)
        topic_solved = create_topic_in_forum(forum, profile, is_solved=True)

        response = self.client.get(reverse("forum:topics-list", args=[category.slug, forum.slug]) + "?filter=solve")

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context["forum"])
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic_solved, response.context["topics"][0])

    def test_success_filter_list_all_topics_unsolved_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic_unsolved = create_topic_in_forum(forum, profile)
        create_topic_in_forum(forum, profile, is_solved=True)

        response = self.client.get(reverse("forum:topics-list", args=[category.slug, forum.slug]) + "?filter=unsolve")

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context["forum"])
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic_unsolved, response.context["topics"][0])

    def test_success_filter_list_all_topics_noanswer_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile)
        create_topic_in_forum(forum, profile, is_solved=True)

        response = self.client.get(reverse("forum:topics-list", args=[category.slug, forum.slug]) + "?filter=noanswer")

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context["forum"])
        self.assertEqual(2, len(response.context["topics"]))


class TopicPostsListViewTest(TestCase):
    def test_failure_list_all_posts_of_a_topic_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")
        profile = ProfileFactory()
        category, forum = create_category_and_forum(group)
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))

        self.assertEqual(403, response.status_code)

    def test_failure_list_all_posts_of_a_topic_with_wrong_slug(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, "x"]))

        self.assertEqual(302, response.status_code)

    def test_success_list_all_posts_of_a_topic(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context["topic"])
        self.assertEqual(1, len(response.context["posts"]))
        self.assertEqual(topic.last_message, response.context["posts"][0])
        self.assertEqual(topic.last_message.pk, response.context["last_post_pk"])
        self.assertIsNotNone(response.context["form"])
        self.assertIsNotNone(response.context["form_move"])

    def test_subscriber_count_of_a_topic(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.context["subscriber_count"])


class TopicNewTest(TestCase):
    def test_failure_create_topic_with_a_post_with_client_unauthenticated(self):
        _, forum = create_category_and_forum()

        response = self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}")

        self.assertEqual(302, response.status_code)

    def test_failure_create_topic_with_a_post_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        _, forum = create_category_and_forum()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}")

        self.assertEqual(403, response.status_code)

    def test_failure_create_topics_with_a_post_in_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")
        profile = ProfileFactory()
        _, forum = create_category_and_forum(group)

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}")

        self.assertEqual(403, response.status_code)

    def test_failure_create_topics_with_a_post_with_wrong_forum(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:topic-new") + "?forum=x")

        self.assertEqual(404, response.status_code)

    def test_success_create_topic_with_a_post_in_get_method(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-new") + f"?forum={forum.pk}")

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context["forum"])
        self.assertIsNotNone(response.context["form"])

    def test_last_read_topic_url(self):
        profile = ProfileFactory()
        profile2 = ProfileFactory()
        notvisited = ProfileFactory()
        _, forum = create_category_and_forum()
        self.client.force_login(profile.user)
        data = {"title": "Title of the topic", "subtitle": "Subtitle of the topic", "text": "A new post!", "tags": ""}
        self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}", data, follow=False)
        self.client.logout()
        self.client.force_login(profile2.user)
        data = {"title": "Title of the topic", "subtitle": "Subtitle of the topic", "text": "A new post!", "tags": ""}
        self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}", data, follow=False)
        self.client.logout()
        self.client.force_login(profile.user)
        topic = Topic.objects.last()
        post = Post.objects.filter(topic__pk=topic.pk).first()
        # for user
        url = topic.resolve_last_read_post_absolute_url()
        self.assertEqual(url, topic.get_absolute_url() + "?page=1#p" + str(post.pk))

        # for anonymous
        self.client.logout()
        self.assertEqual(url, topic.get_absolute_url() + "?page=1#p" + str(post.pk))
        # for no visit
        self.client.force_login(notvisited.user)
        self.assertEqual(url, topic.get_absolute_url() + "?page=1#p" + str(post.pk))

    def test_success_create_topic_with_post_in_preview_in_ajax(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()

        self.client.force_login(profile.user)
        data = {"preview": "", "text": "A new post!"}
        response = self.client.post(
            reverse("forum:topic-new") + f"?forum={forum.pk}",
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            follow=False,
        )

        self.assertEqual(200, response.status_code)

    def test_success_create_topic_with_post_in_preview(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()

        self.client.force_login(profile.user)
        data = {
            "preview": "",
            "title": "Title of the topic",
            "subtitle": "Subtitle of the topic",
            "text": "A new post!",
        }
        response = self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}", data, follow=False)

        self.assertEqual(200, response.status_code)

    def test_success_create_topic_with_post(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()

        self.client.force_login(profile.user)
        data = {"title": "Title of the topic", "subtitle": "Subtitle of the topic", "text": "A new post!", "tags": ""}
        response = self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)

    def test_create_topic_with_hat(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()

        hat, _ = Hat.objects.get_or_create(name__iexact="A hat", defaults={"name": "A hat"})
        profile.hats.add(hat)

        self.client.force_login(profile.user)
        data = {
            "title": "Title of the topic",
            "subtitle": "Subtitle of the topic",
            "text": "A new post!",
            "tags": "",
            "with_hat": hat.pk,
        }
        response = self.client.post(reverse("forum:topic-new") + f"?forum={forum.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertEqual(Post.objects.latest("pubdate").hat, hat)


class TopicEditTest(TestCase):
    def test_failure_edit_topic_with_client_unauthenticated(self):
        response = self.client.post(reverse("forum:topic-edit"))

        self.assertEqual(302, response.status_code)

    def test_failure_edit_topic_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:topic-edit"))

        self.assertEqual(403, response.status_code)

    def test_failure_edit_topic_with_wrong_topic_pk(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(
            reverse("forum:topic-edit"),
            {
                "topic": "abc",
            },
            follow=False,
        )

        self.assertEqual(404, response.status_code)

    def test_failure_edit_topic_with_a_topic_not_found(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(
            reverse("forum:topic-edit"),
            {
                "topic": 99999,
            },
            follow=False,
        )

        self.assertEqual(404, response.status_code)

    def test_success_edit_topic_in_ajax(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"topic": topic.pk}
        response = self.client.post(
            reverse("forum:topic-edit"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest", follow=False
        )

        self.assertEqual(200, response.status_code)

    def test_success_edit_topic(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)

    def test_success_edit_topic_follow(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"follow": "1"}
        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(profile.user, topic, is_active=False))

        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(profile.user, topic, is_active=True))

    def test_success_edit_topic_follow_with_hidden_post(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        first_post = topic.first_post()
        first_post.is_visible = False
        first_post.save()

        self.client.force_login(profile.user)
        data = {"follow": "1"}
        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(profile.user, topic, is_active=False))

        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(profile.user, topic, is_active=True))

    def test_success_edit_topic_follow_email(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"email": "1"}
        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(
            TopicAnswerSubscription.objects.get_existing(profile.user, topic, is_active=True, by_email=True)
        )

        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(
            TopicAnswerSubscription.objects.get_existing(profile.user, topic, is_active=True, by_email=False)
        )

    def test_failure_edit_topic_solved_not_author(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        self.client.force_login(profile.user)
        data = {"solved": "", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_solved_by_author(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"solved": "", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)
        self.assertTrue(topic.is_solved)
        self.assertEqual(topic.solved_by, profile.user)

    def test_success_edit_topic_solved_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(staff.user)
        data = {"solved": "", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)
        self.assertTrue(topic.is_solved)
        self.assertEqual(topic.solved_by, staff.user)

    def test_failure_edit_topic_lock_by_user(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        self.client.force_login(profile.user)
        data = {"lock": "true", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_lock_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(staff.user)
        data = {"lock": "true", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_locked)

        data = {"lock": "false", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertFalse(Topic.objects.get(pk=topic.pk).is_locked)

    def test_failure_edit_topic_sticky_by_user(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        self.client.force_login(profile.user)
        data = {"sticky": "true", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_sticky_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(staff.user)
        data = {"sticky": "true", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_sticky)

        data = {"sticky": "false", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertFalse(Topic.objects.get(pk=topic.pk).is_sticky)

    @patch("zds.forum.signals.topic_moved")
    def test_failure_edit_topic_move_by_user(self, topic_moved):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        self.client.force_login(profile.user)
        data = {"move": "", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(topic_moved.send.call_count, 0)
        self.assertEqual(403, response.status_code)

    @patch("zds.forum.signals.topic_moved")
    def test_failure_edit_topic_move_with_wrong_forum_pk_by_staff(self, topic_moved):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(staff.user)
        data = {"move": "", "forum": "abc", "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(topic_moved.send.call_count, 0)
        self.assertEqual(404, response.status_code)

    @patch("zds.forum.signals.topic_moved")
    def test_failure_edit_topic_move_with_a_forum_not_found_by_staff(self, topic_moved):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(staff.user)
        data = {"move": "", "forum": 99999, "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(topic_moved.send.call_count, 0)
        self.assertEqual(404, response.status_code)

    @patch("zds.forum.signals.topic_moved")
    def test_success_edit_topic_move_by_staff(self, topic_moved):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        _, another_forum = create_category_and_forum()

        self.client.force_login(staff.user)
        data = {"move": "", "forum": another_forum.pk, "topic": topic.pk}
        response = self.client.post(reverse("forum:topic-edit"), data, follow=False)

        self.assertEqual(topic_moved.send.call_count, 1)
        self.assertEqual(302, response.status_code)

    def test_failure_edit_topic_not_author_and_not_staff(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        another_profile = ProfileFactory()
        self.client.force_login(another_profile.user)
        response = self.client.get(reverse("forum:topic-edit") + f"?topic={topic.pk}", follow=False)
        self.assertEqual(403, response.status_code)

        data = {"text": "New text for the post"}
        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)
        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_staff_in_get_method(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(staff.user)
        response = self.client.get(reverse("forum:topic-edit") + f"?topic={topic.pk}", follow=False)

        self.assertEqual(200, response.status_code)

    def test_success_edit_topic_author_in_get_method(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-edit") + f"?topic={topic.pk}", follow=False)

        self.assertEqual(200, response.status_code)

    def test_success_edit_topic_in_preview(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {
            "preview": "",
            "title": "New title",
            "subtitle": "New subtitle",
            "text": "A new post!",
        }
        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context["topic"])
        self.assertIsNotNone(response.context["form"])

    def test_success_edit_topic_in_preview_in_ajax(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {
            "preview": "",
            "title": "New title",
            "subtitle": "New subtitle",
            "text": "A new post!",
        }
        response = self.client.post(
            reverse("forum:topic-edit") + f"?topic={topic.pk}",
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            follow=False,
        )

        self.assertEqual(200, response.status_code)

    def test_success_edit_topic_information(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {
            "title": "New title",
            "subtitle": "New subtitle",
            "text": "A new post!",
        }
        response = self.client.post(reverse("forum:topic-edit") + f"?topic={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)
        post = Post.objects.get(topic__pk=topic.pk)
        self.assertEqual(data.get("title"), topic.title)
        self.assertEqual(data.get("subtitle"), topic.subtitle)
        self.assertEqual(data.get("text"), post.text)


class FindTopicTest(TestCase):
    def test_failure_find_topics_of_a_member_not_found(self):
        response = self.client.get(reverse("forum:topic-find", args=[9999]), follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_find_topics_of_a_member(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:topic-find", args=[profile.user.pk]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])

    def test_success_find_topics_of_a_member_private_forum(self):
        """
        Test that when a user is part of two groups and that those groups can both read a private forum
        only one topic is returned by the query (cf. Issue 4068).
        """
        profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        another_group = Group.objects.create(name="DummyGroup_2")
        _, forum = create_category_and_forum(group)

        forum.groups.add(another_group)
        forum.save()

        profile.user.groups.add(group)
        profile.user.groups.add(another_group)
        profile.user.save()

        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-find", args=[profile.user.pk]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])


class FindFollowedTopicTest(TestCase):
    def test_public_cant_access_followed_topics(self):
        response = self.client.get(reverse("forum:followed-topic-find"), follow=False)
        self.assertEqual(302, response.status_code)
        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("forum:followed-topic-find"))

    def test_success_find_followed_topics_of_a_member(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:followed-topic-find"), follow=False)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])


class FindTopicByTagTest(TestCase):
    def test_failure_find_topics_of_a_tag_not_found(self):
        response = self.client.get(reverse("forum:topic-tag-find", args=["x"]), follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_find_topics_of_a_tag(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        tag = TagFactory()
        topic.add_tags([tag.title])

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-tag-find", args=[tag.slug]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])
        self.assertEqual(tag, response.context["tag"])

    def test_success_find_topics_of_a_tag_private_forums(self):
        """
        Test that when a user is part of two groups and that those groups can both read a private forum
        only one topic is returned by the query (cf. Issue 4068).
        """
        profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        another_group = Group.objects.create(name="DummyGroup_2")
        _, forum = create_category_and_forum(group)

        forum.groups.add(another_group)
        forum.save()

        profile.user.groups.add(group)
        profile.user.groups.add(another_group)
        profile.user.save()

        topic = create_topic_in_forum(forum, profile)
        tag = TagFactory()
        topic.add_tags([tag.title])

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-tag-find", args=[tag.slug]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic, response.context["topics"][0])
        self.assertEqual(tag, response.context["tag"])

    def test_success_find_topics_of_a_tag_solved(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile)
        topic_solved = create_topic_in_forum(forum, profile, is_solved=True)
        tag = TagFactory()
        topic_solved.add_tags([tag.title])

        response = self.client.get(reverse("forum:topic-tag-find", args=[tag.slug]) + "?filter=solve")

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic_solved, response.context["topics"][0])
        self.assertEqual(tag, response.context["tag"])

    def test_success_filter_find_topics_of_a_tag_unsolved(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile, is_solved=True)
        topic_unsolved = create_topic_in_forum(forum, profile)
        tag = TagFactory()
        topic_unsolved.add_tags([tag.title])

        response = self.client.get(reverse("forum:topic-tag-find", args=[tag.slug]) + "?filter=unsolve")

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(topic_unsolved, response.context["topics"][0])
        self.assertEqual(tag, response.context["tag"])

    def test_success_filter_find_topics_of_a_tag_noanswer(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_topic = create_topic_in_forum(forum, profile, is_solved=True)
        tag = TagFactory()
        topic.add_tags([tag.title])
        another_topic.add_tags([tag.title])

        response = self.client.get(reverse("forum:topic-tag-find", args=[tag.slug]) + "?filter=noanswer")

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.context["topics"]))
        self.assertEqual(tag, response.context["tag"])

    def test_redirection(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        create_topic_in_forum(forum, profile)
        topic_solved = create_topic_in_forum(forum, profile, is_solved=True)
        tag = TagFactory()
        topic_solved.add_tags([tag.title])

        response = self.client.get(reverse("forum:old-topic-tag-find", args=[tag.pk, tag.slug]))
        self.assertEqual(301, response.status_code)

        response = self.client.get(reverse("forum:old-topic-tag-find", args=[tag.pk, tag.slug]), follow=True)
        self.assertEqual(1, len(response.context["topics"]))
        self.assertEqual(tag, response.context["tag"])


class PostNewTest(TestCase):
    def test_failure_new_post_with_client_unauthenticated(self):
        response = self.client.post(reverse("forum:post-new"))

        self.assertEqual(302, response.status_code)

    def test_failure_new_post_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-new"))

        self.assertEqual(403, response.status_code)

    def test_failure_new_post_with_wrong_topic_pk(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-new") + "?sujet=abc", follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_new_post_with_a_topic_not_found(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-new") + "?sujet=99999", follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_new_post_in_a_forum_we_cannot_read(self):
        profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        _, forum = create_category_and_forum(group)
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-new") + f"?sujet={topic.pk}")

        self.assertEqual(403, response.status_code)

    def test_failure_new_post_on_a_locked_topic(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile, is_locked=True)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-new") + f"?sujet={topic.pk}")

        self.assertEqual(403, response.status_code)

    def test_failure_new_post_stopped_by_anti_spam(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        topic.last_message.pubdate = datetime.now()
        topic.last_message.save()

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-new") + f"?sujet={topic.pk}")

        self.assertEqual(403, response.status_code)

    def test_success_new_post_method_get(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-new") + f"?sujet={topic.pk}", follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context["topic"])
        self.assertEqual(topic.last_message, response.context["posts"][0])
        self.assertEqual(topic.last_message.pk, response.context["last_post_pk"])
        self.assertIsNotNone(response.context["form"])

    def test_success_new_post_with_quote_in_ajax(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.get(
            reverse("forum:post-new") + f"?sujet={topic.pk}&cite={topic.last_message.pk}",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            follow=False,
        )

        self.assertEqual(200, response.status_code)

    def test_success_new_post_in_preview(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        data = {"preview": "", "text": "A new post!", "last_post": topic.last_message.pk}
        response = self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context["topic"])
        self.assertEqual(topic.last_message, response.context["posts"][0])
        self.assertEqual(topic.last_message.pk, response.context["last_post_pk"])
        self.assertIsNotNone(response.context["form"])

    def test_success_new_post_in_preview_in_ajax(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        data = {"preview": "", "text": "A new post!", "last_post": topic.last_message.pk}
        response = self.client.post(
            reverse("forum:post-new") + f"?sujet={topic.pk}",
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            follow=False,
        )

        self.assertEqual(200, response.status_code)

    def test_success_new_post(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        data = {"text": "A new post!", "last_post": topic.last_message.pk}
        response = self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertEqual(2, Post.objects.filter(topic__pk=topic.pk).count())

    def test_new_post_with_hat(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()

        profile = ProfileFactory()

        self.client.force_login(profile.user)

        hat, _ = Hat.objects.get_or_create(name__iexact="A hat", defaults={"name": "A hat"})
        other_hat, _ = Hat.objects.get_or_create(name__iexact="Another hat", defaults={"name": "Another hat"})

        # Add a hat to profile
        profile.hats.add(hat)

        # Post with a wrong hat pk
        topic = create_topic_in_forum(forum, another_profile)
        data = {
            "text": "A new post!",
            "last_post": topic.last_message.pk,
            "with_hat": "abc",
        }
        response = self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)
        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(2, Post.objects.filter(topic__pk=topic.pk).count())
        self.assertEqual(topic.last_message.hat, None)  # Hat wasn't used

        # Post with a hat that doesn't exist
        topic = create_topic_in_forum(forum, another_profile)
        data = {
            "text": "A new post!",
            "last_post": topic.last_message.pk,
            "with_hat": 1587,
        }
        response = self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)
        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(2, Post.objects.filter(topic__pk=topic.pk).count())
        self.assertEqual(topic.last_message.hat, None)  # Hat wasn't used

        # Post with a hat the user hasn't
        topic = create_topic_in_forum(forum, another_profile)
        data = {
            "text": "A new post!",
            "last_post": topic.last_message.pk,
            "with_hat": other_hat.pk,
        }
        response = self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)
        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(2, Post.objects.filter(topic__pk=topic.pk).count())
        self.assertEqual(topic.last_message.hat, None)  # Hat wasn't used

        # Post with a hat the user has
        topic = create_topic_in_forum(forum, another_profile)
        data = {
            "text": "A new post!",
            "last_post": topic.last_message.pk,
            "with_hat": hat.pk,
        }
        response = self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)
        self.assertEqual(302, response.status_code)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(2, Post.objects.filter(topic__pk=topic.pk).count())
        self.assertEqual(topic.last_message.hat, hat)  # Hat was used


class PostEditTest(TestCase):
    def test_failure_edit_post_with_client_unauthenticated(self):
        response = self.client.post(reverse("forum:post-edit"))

        self.assertEqual(302, response.status_code)

    def test_failure_edit_post_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-edit"))

        self.assertEqual(403, response.status_code)

    def test_failure_edit_post_with_wrong_post_pk(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-edit") + "?message=abc", follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_edit_post_with_a_topic_not_found(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-edit") + "?message=99999", follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_edit_post_in_a_forum_we_cannot_read(self):
        profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        _, forum = create_category_and_forum(group)
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-edit") + f"?message={topic.last_message.pk}")

        self.assertEqual(403, response.status_code)

    def test_failure_edit_post_not_author_not_staff_and_not_alert_message(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-edit") + f"?message={topic.last_message.pk}")

        self.assertEqual(403, response.status_code)

    def test_success_edit_post_method_get(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-edit") + f"?message={topic.last_message.pk}", follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context["topic"])
        self.assertEqual(topic.last_message, response.context["post"])
        self.assertEqual(topic.last_message.text, response.context["text"])
        self.assertIsNotNone(response.context["form"])

    def test_success_new_post_in_preview(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"preview": "", "text": "A new post!"}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(200, response.status_code)

    def test_success_edit_post_in_preview_in_ajax(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {
            "preview": "",
            "text": "A new post!",
        }
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}",
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            follow=False,
        )

        self.assertEqual(200, response.status_code)

    def test_success_edit_post(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"text": "A new post!"}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(302, response.status_code)
        post = Post.objects.get(pk=topic.last_message.pk)
        self.assertEqual(profile.user, post.editor)
        self.assertEqual(data.get("text"), post.text)

    def test_failure_edit_post_hide_message_not_author_and_not_staff(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        data = {"delete_message": ""}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(403, response.status_code)

    def test_success_edit_post_hide_message_by_author(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        # WARNING : if author is not staff he can't send a delete message.
        data = {"delete_message": ""}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(302, response.status_code)
        post = Post.objects.get(pk=topic.last_message.pk)
        self.assertEqual(0, len(post.alerts_on_this_comment.all()))
        self.assertFalse(post.is_visible)
        self.assertEqual(profile.user, post.editor)
        self.assertEqual("", post.text_hidden)

    def test_success_edit_post_hide_message_by_staff(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        text_hidden_expected = "Bad guy!"
        data = {"delete_message": "", "text_hidden": text_hidden_expected}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(302, response.status_code)
        post = Post.objects.get(pk=topic.last_message.pk)
        self.assertEqual(0, len(post.alerts_on_this_comment.all()))
        self.assertFalse(post.is_visible)
        self.assertEqual(staff.user, post.editor)
        self.assertEqual(text_hidden_expected, post.text_hidden)

    def test_hide_helpful_message(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + f"?message={topic.last_message.pk}", follow=False)
        self.assertEqual(302, response.status_code)

        response = self.client.get(topic.get_absolute_url(), follow=False)
        self.assertNotContains(response, "green hidden")

        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", {"delete_message": ""}, follow=False
        )
        self.assertEqual(302, response.status_code)

        response = self.client.get(topic.get_absolute_url(), follow=False)
        self.assertContains(response, "green hidden")

    def test_failure_edit_post_show_message_by_user(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        data = {"show_message": ""}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(403, response.status_code)

    def test_failure_edit_post_show_message_by_author(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"show_message": ""}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(403, response.status_code)

    def test_success_edit_post_show_message_by_staff(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        topic.last_message.is_visible = False
        topic.last_message.text_hidden = "Bad guy!"
        topic.last_message.save()

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        data = {
            "show_message": "",
        }
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(302, response.status_code)
        post = Post.objects.get(pk=topic.last_message.pk)
        self.assertTrue(post.is_visible)
        self.assertEqual("", post.text_hidden)

    def test_success_edit_post_alert_message(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        text_expected = "Bad guy!"
        data = {"signal_message": "", "signal_text": text_expected}
        response = self.client.post(
            reverse("forum:post-create-alert") + f"?message={topic.last_message.pk}", data, follow=False
        )

        self.assertEqual(302, response.status_code)
        post = Post.objects.get(pk=topic.last_message.pk)
        self.assertEqual(1, len(post.alerts_on_this_comment.all()))
        self.assertEqual(text_expected, post.alerts_on_this_comment.all()[0].text)

    def test_failure_edit_post_hidden_message_by_non_staff(self):
        """Test that a non staff cannot access the page to edit a hidden message"""

        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        data = {"delete_message": ""}

        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )
        self.assertEqual(302, response.status_code)

        response = self.client.get(reverse("forum:post-edit") + f"?message={topic.last_message.pk}")
        self.assertEqual(403, response.status_code)

        response = self.client.get(reverse("forum:topic-edit") + f"?topic={topic.pk}", follow=False)
        self.assertEqual(403, response.status_code)

    def test_hat_edit(self):
        profile = ProfileFactory()
        hat, _ = Hat.objects.get_or_create(name__iexact="A hat", defaults={"name": "A hat"})
        other_hat, _ = Hat.objects.get_or_create(name__iexact="Another hat", defaults={"name": "Another hat"})
        profile.hats.add(hat)

        # add a new thread
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, ProfileFactory())

        # post a message with a hat
        self.client.force_login(profile.user)
        data = {
            "text": "A new post!",
            "last_post": topic.last_message.pk,
            "with_hat": hat.pk,
        }
        self.client.post(reverse("forum:post-new") + f"?sujet={topic.pk}", data, follow=False)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(topic.last_message.hat, hat)  # Hat was used

        # test that it's possible to remove the hat
        data = {"text": "A new post!"}
        self.client.post(reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(topic.last_message.hat, None)  # Hat was removed

        # test that it's impossible to use a hat the user hasn't
        data = {
            "text": "A new post!",
            "with_hat": other_hat.pk,
        }
        self.client.post(reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(topic.last_message.hat, None)  # Hat wasn't used

        # but check that it's possible to use a hat the user has
        profile.hats.add(other_hat)
        data = {
            "text": "A new post!",
            "with_hat": other_hat.pk,
        }
        self.client.post(reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False)
        topic = Topic.objects.get(pk=topic.pk)  # refresh
        self.assertEqual(topic.last_message.hat, other_hat)  # Now, it works

    def test_creation_archive_on_edit(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        post_before_edit = Post.objects.get(pk=topic.last_message.pk)

        post_before_edit.save(search_engine_requires_index=False)

        edits_count = CommentEdit.objects.count()

        # Edit post
        self.client.force_login(profile.user)
        data = {"text": "A new post!"}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )
        self.assertEqual(302, response.status_code)

        # Check that an archive was created
        self.assertEqual(CommentEdit.objects.count(), edits_count + 1)

        # Check the archive content
        edit = CommentEdit.objects.latest("date")
        self.assertEqual(post_before_edit.pk, edit.comment.pk)
        self.assertEqual(post_before_edit.text, edit.original_text)
        self.assertEqual(profile.user, edit.editor)

        # Check the post was marked as to reindex
        post_before_edit.refresh_from_db()
        self.assertTrue(post_before_edit.search_engine_requires_index)


class PostUsefulTest(TestCase):
    def test_failure_post_useful_require_method_post(self):
        response = self.client.get(reverse("forum:post-useful"), follow=False)

        self.assertEqual(405, response.status_code)

    def test_failure_post_useful_with_client_unauthenticated(self):
        response = self.client.post(reverse("forum:post-useful"), follow=False)

        self.assertEqual(302, response.status_code)

    def test_failure_post_useful_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful"))

        self.assertEqual(403, response.status_code)

    def test_failure_post_useful_with_wrong_topic_pk(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + "?message=abc", follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_post_useful_with_a_topic_not_found(self):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + "?message=99999", follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_post_useful_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        _, forum = create_category_and_forum(group)
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + f"?message={topic.last_message.pk}")

        self.assertEqual(403, response.status_code)

    def test_failure_post_useful_its_post(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + f"?message={topic.last_message.pk}")

        self.assertEqual(302, response.status_code)

    def test_failure_post_useful_when_not_author_of_topic(self):
        another_profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, another_profile)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + f"?message={topic.last_message.pk}")

        self.assertEqual(403, response.status_code)

    def test_success_post_useful_in_ajax(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.client.force_login(profile.user)
        response = self.client.post(
            reverse("forum:post-useful") + f"?message={post.pk}", HTTP_X_REQUESTED_WITH="XMLHttpRequest", follow=False
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(Post.objects.get(pk=post.pk).is_useful)

    def test_success_post_useful(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.client.force_login(profile.user)
        response = self.client.post(reverse("forum:post-useful") + f"?message={post.pk}", follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Post.objects.get(pk=post.pk).is_useful)

    def test_success_post_useful_by_staff(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        response = self.client.post(reverse("forum:post-useful") + f"?message={topic.last_message.pk}", follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Post.objects.get(pk=topic.last_message.pk).is_useful)

    def test_position_post_useful_button(self):
        """
        The “Useful message” button should be:
        - for logged-out users, nowhere;
        - for normal users, under the message on their own threads, nowhere else;
        - for staff, under the message on their own thread, on the menu else.
        """
        mark_button_under_message = "Cette réponse m’a été utile"
        mark_button_in_menu = "Réponse utile"

        user = ProfileFactory()
        staff = StaffProfileFactory()

        _, forum = create_category_and_forum()
        user_topic = create_topic_in_forum(forum, user)
        staff_topic = create_topic_in_forum(forum, staff)

        # Logged-out users should not see any “useful message” button

        self.client.logout()
        response = self.client.get(reverse("forum:topic-posts-list", args=[user_topic.pk, user_topic.slug()]))
        self.assertNotContains(response, mark_button_under_message)
        self.assertNotContains(response, mark_button_in_menu)

        # Normal users should see the “useful message” button on their topics but
        # not on other ones.

        self.client.force_login(user.user)

        response = self.client.get(reverse("forum:topic-posts-list", args=[user_topic.pk, user_topic.slug()]))
        self.assertContains(response, mark_button_under_message)
        self.assertNotContains(response, mark_button_in_menu)

        response = self.client.get(reverse("forum:topic-posts-list", args=[staff_topic.pk, staff_topic.slug()]))
        self.assertNotContains(response, mark_button_under_message)
        self.assertNotContains(response, mark_button_in_menu)

        # Staff users should see the “useful message” button on their topics and
        # other ones, but the button should be in the menu for other topics.

        self.client.force_login(staff.user)

        response = self.client.get(reverse("forum:topic-posts-list", args=[user_topic.pk, user_topic.slug()]))
        self.assertNotContains(response, mark_button_under_message)
        self.assertContains(response, mark_button_in_menu)

        response = self.client.get(reverse("forum:topic-posts-list", args=[staff_topic.pk, staff_topic.slug()]))
        self.assertContains(response, mark_button_under_message)
        self.assertNotContains(response, mark_button_in_menu)


class MessageActionTest(TestCase):
    def test_alert(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        PostFactory(topic=topic, author=another_profile.user, position=2)

        # unauthenticated, no 'Alert' button
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertNotContains(response, "Signaler")

        # authenticated, two 'Alert' buttons because we have two messages
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        alerts = [word for word in str(response.content).split() if word == "alert"]
        self.assertEqual(len(alerts), 2)

        # staff hides a message
        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        text_hidden_expected = "Bad guy!"
        data = {"delete_message": "", "text_hidden": text_hidden_expected}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )
        self.assertEqual(302, response.status_code)

        # staff can alert all messages
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertContains(response, '<a href="#signal-message-', count=2)

        # authenticated, user can alert the hidden message too
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertContains(response, '<a href="#signal-message-', count=2)

    def test_hide(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        PostFactory(topic=topic, author=another_profile.user, position=2)

        # two posts are displayed
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        posts = [word for word in response.content.decode().split() if word == "m'appelle"]
        self.assertEqual(len(posts), 2)

        # unauthenticated, no 'Hide' button
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertNotContains(response, "Masquer")

        # authenticated, only one 'Hide' buttons because our user only posted one of them
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        hide_buttons = [word for word in response.content.decode().split() if word == "hide"]
        self.assertEqual(len(hide_buttons), 1)

        # staff hides a message
        staff = StaffProfileFactory()
        self.client.force_login(staff.user)
        text_hidden_expected = "Bad guy!"
        data = {"delete_message": "", "text_hidden": text_hidden_expected}
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )
        self.assertEqual(302, response.status_code)

        # unauthenticated
        # only one post is displayed, visitor can see hide reason and cannot show or re-enable
        self.client.logout()
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        posts = [word for word in response.content.decode().split() if word == "m'appelle"]
        self.assertEqual(len(posts), 1)
        self.assertNotContains(response, '<details class="message-text message-hidden-container">')
        self.assertNotContains(response, "Démasquer")
        self.assertContains(response, "Bad guy!")

        # user cannot show or re-enable their message
        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertNotContains(response, '<details class="message-text message-hidden-container">')
        self.assertNotContains(response, "Démasquer")
        self.assertContains(response, "Bad guy!")

        # staff can show or re-enable
        self.client.force_login(staff.user)
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        self.assertContains(response, '<details class="message-text message-hidden-container">')
        self.assertContains(response, "Démasquer")
        self.assertContains(response, "Bad guy!")

        data = {
            "show_message": "",
        }
        response = self.client.post(
            reverse("forum:post-edit") + f"?message={topic.last_message.pk}", data, follow=False
        )
        self.assertEqual(302, response.status_code)

        # two posts are displayed again
        self.client.logout()
        response = self.client.get(reverse("forum:topic-posts-list", args=[topic.pk, topic.slug()]))
        posts = [word for word in response.content.decode().split() if word == "m'appelle"]
        self.assertEqual(len(posts), 2)


class PostUnreadTest(TestCase):
    @patch("zds.forum.signals.post_unread")
    def test_failure_post_unread_require_method_get(self, post_unread):
        response = self.client.post(reverse("forum:post-unread"), follow=False)
        self.assertEqual(post_unread.send.call_count, 0)
        self.assertEqual(405, response.status_code)

    @patch("zds.forum.signals.post_unread")
    def test_failure_post_unread_with_client_unauthenticated(self, post_unread):
        response = self.client.get(reverse("forum:post-unread"), follow=False)
        self.assertEqual(post_unread.send.call_count, 0)
        self.assertEqual(302, response.status_code)

    @patch("zds.forum.signals.post_unread")
    def test_failure_post_unread_with_sanctioned_user(self, post_unread):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-unread"))

        self.assertEqual(post_unread.send.call_count, 0)
        self.assertEqual(403, response.status_code)

    @patch("zds.forum.signals.post_unread")
    def test_failure_post_unread_with_wrong_topic_pk(self, post_unread):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-unread") + "?message=abc", follow=False)

        self.assertEqual(post_unread.send.call_count, 0)
        self.assertEqual(404, response.status_code)

    @patch("zds.forum.signals.post_unread")
    def test_failure_post_unread_with_a_topic_not_found(self, post_unread):
        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-unread") + "?message=99999", follow=False)

        self.assertEqual(post_unread.send.call_count, 0)
        self.assertEqual(404, response.status_code)

    @patch("zds.forum.signals.post_unread")
    def test_failure_post_unread_of_a_forum_we_cannot_read(self, post_unread):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        _, forum = create_category_and_forum(group)
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-unread") + f"?message={topic.last_message.pk}")

        self.assertEqual(post_unread.send.call_count, 0)
        self.assertEqual(403, response.status_code)

    @patch("zds.forum.signals.post_unread")
    def test_success_post_unread(self, post_unread):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-unread") + f"?message={post.pk}", follow=False)

        self.assertEqual(post_unread.send.call_count, 1)
        self.assertEqual(302, response.status_code)


class FindPostTest(TestCase):
    def test_failure_find_topics_of_a_member_not_found(self):
        response = self.client.get(reverse("forum:post-find", args=[9999]), follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_find_topics_of_a_member(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)

        response = self.client.get(reverse("forum:post-find", args=[profile.user.pk]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["posts"]))
        self.assertEqual(topic.last_message, response.context["posts"][0])

    def test_success_find_topics_of_a_member_private_forum(self):
        """
        Test that when a user is part of two groups and that those groups can both read a private forum
        only one post is returned by the query (cf. Issue 4068).
        """
        profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        another_group = Group.objects.create(name="DummyGroup_2")
        _, forum = create_category_and_forum(group)

        forum.groups.add(another_group)
        forum.save()

        profile.user.groups.add(group)
        profile.user.groups.add(another_group)
        profile.user.save()

        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.get(reverse("forum:post-find", args=[profile.user.pk]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["posts"]))
        self.assertEqual(topic.last_message, response.context["posts"][0])


class ShowLinksGitHubIssueTest(TestCase):
    """
    Test if buttons to manage GitHub issues are correctly displayed according to the context.
    """

    def setUp(self):
        profile = ProfileFactory()
        self.dev_profile = DevProfileFactory()
        category, forum = create_category_and_forum()
        self.unlinked_topic = create_topic_in_forum(forum, profile)
        self.linked_topic = create_topic_in_forum(forum, profile)
        self.linked_topic.github_repository_name = settings.ZDS_APP["github_projects"]["repositories"][0]
        self.linked_topic.github_issue = 42
        self.linked_topic.save()

        self.route = "forum:topic-posts-list"
        self.label_linked_issue = _("Ticket associé")
        self.label_unlink_issue = _("Dissocier le ticket")
        self.label_create_issue = _("Créer un ticket")
        self.label_link_issue = _("Associer un ticket")

    def test_default(self):
        """
        Default: nothing is displayed
        """
        response = self.client.get(reverse(self.route, args=[self.unlinked_topic.pk, self.unlinked_topic.slug()]))
        self.assertNotContains(response, self.label_linked_issue)
        self.assertNotContains(response, self.label_unlink_issue)
        self.assertNotContains(response, self.label_create_issue)
        self.assertNotContains(response, self.label_link_issue)

    def test_associated_issue(self):
        """
        An issue is associated: the link is displayed
        """
        response = self.client.get(reverse(self.route, args=[self.linked_topic.pk, self.linked_topic.slug()]))
        self.assertContains(response, self.label_linked_issue)
        self.assertNotContains(response, self.label_unlink_issue)
        self.assertNotContains(response, self.label_create_issue)
        self.assertNotContains(response, self.label_link_issue)

    def test_no_ticket_logged_as_dev(self):
        """
        Logged as a dev member, no ticket is associated: buttons to link or create an issue are displayed
        """
        self.client.force_login(self.dev_profile.user)
        response = self.client.get(reverse(self.route, args=[self.unlinked_topic.pk, self.unlinked_topic.slug()]))
        self.assertNotContains(response, self.label_linked_issue)
        self.assertNotContains(response, self.label_unlink_issue)
        self.assertContains(response, self.label_create_issue)
        self.assertContains(response, self.label_link_issue)

    def test_ticket_logged_as_dev(self):
        """
        Logged as a dev member, a ticket is associated: buttons to unlink or view the issue are displayed
        """
        self.client.force_login(self.dev_profile.user)
        response = self.client.get(reverse(self.route, args=[self.linked_topic.pk, self.linked_topic.slug()]))
        self.assertContains(response, self.label_linked_issue)
        self.assertContains(response, self.label_unlink_issue)
        self.assertNotContains(response, self.label_create_issue)
        self.assertNotContains(response, self.label_link_issue)
