from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, UserFactory
from zds.mp.models import PrivatePost, PrivateTopic, PrivateTopicRead, mark_read
from zds.mp.tests.factories import PrivatePostFactory, PrivateTopicFactory
from zds.utils.models import Hat


class IndexViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

    def test_success_delete_topic_no_participants(self):
        topic = PrivateTopicFactory(author=self.profile1.user)
        self.client.force_login(self.profile1.user)
        self.assertEqual(1, PrivateTopic.objects.filter(pk=topic.pk).count())

        response = self.client.post(reverse("mp:list-delete"), {"items": [topic.pk]})

        self.assertEqual(302, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=topic.pk).count())

    def test_success_delete_topic_as_author(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(reverse("mp:list-delete"), {"items": [self.topic1.pk]})

        self.assertEqual(302, response.status_code)
        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertEqual(self.profile2.user, topic.author)
        self.assertNotIn(self.profile1.user, topic.participants.all())
        self.assertNotIn(self.profile2.user, topic.participants.all())

    def test_success_delete_topic_as_participant(self):
        self.client.force_login(self.profile2.user)

        response = self.client.post(reverse("mp:list-delete"), {"items": [self.topic1.pk]})

        self.assertEqual(302, response.status_code)

        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertNotEqual(self.profile2.user, topic.author)
        self.assertNotIn(self.profile1.user, topic.participants.all())
        self.assertNotIn(self.profile2.user, topic.participants.all())

    def test_fail_delete_topic_not_belong_to_user(self):
        topic = PrivateTopicFactory(author=self.profile1.user)

        self.assertEqual(1, PrivateTopic.objects.filter(pk=topic.pk).count())

        self.client.force_login(self.profile2.user)

        self.client.post(reverse("mp:list-delete"), {"items": [topic.pk]})

        self.assertEqual(1, PrivateTopic.objects.filter(pk=topic.pk).count())

    def test_topic_get_weird_page(self):
        """get a page that can't exist (like page=abc)"""

        self.client.force_login(self.profile1.user)

        response = self.client.get(reverse("mp:list") + "?page=abc")
        self.assertEqual(response.status_code, 404)

    def test_topic_get_page_too_far(self):
        """get a page that is too far yet"""

        self.client.force_login(self.profile1.user)

        # create many subjects (at least two pages)
        for i in range(1, settings.ZDS_APP["forum"]["topics_per_page"] + 5):
            topic = PrivateTopicFactory(author=self.profile1.user)
            topic.participants.add(self.profile2.user)
            PrivatePostFactory(privatetopic=topic, author=self.profile1.user, position_in_topic=1)

        response = self.client.get(reverse("mp:list") + "?page=42")
        self.assertEqual(response.status_code, 404)


class OldViewTest(TestCase):
    """Test the view redirecting former topic URLs to the new ones."""

    def test_nominal(self):
        """Test the redirection on a nominal case."""
        user = ProfileFactory().user
        topic = PrivateTopicFactory(author=user)
        PrivatePostFactory(privatetopic=topic, author=user, position_in_topic=1)

        url_args = {"pk": topic.pk, "topic_slug": topic.slug()}
        url = reverse("mp:old-view", kwargs=url_args)

        self.client.force_login(user)
        response = self.client.get(url)

        redirect_url = reverse("mp:view", kwargs=url_args)
        self.assertRedirects(response, redirect_url, status_code=301)


class TopicViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

    def test_fail_topic_no_exist(self):
        self.client.force_login(self.profile1.user)

        response = self.client.get(reverse("mp:view", args=[12, "private-topic"]))
        self.assertEqual(404, response.status_code)

    def test_fail_topic_no_permission(self):
        """Check that a member not participating in a private topic is forbidden to view it."""

        self.client.force_login(self.profile3.user)

        response = self.client.get(reverse("mp:view", args=[self.topic1.pk, self.topic1.slug()]), follow=True)

        self.assertEqual(403, response.status_code)

    def test_get_weird_page(self):
        """get a page that can't exist (like page=abc)"""

        self.client.force_login(self.profile1.user)

        response = self.client.get(
            reverse(
                "mp:view",
                kwargs={
                    "pk": self.topic1.pk,
                    "topic_slug": self.topic1.slug(),
                },
            )
            + "?page=abc"
        )
        self.assertEqual(response.status_code, 404)

    def test_get_page_too_far(self):
        """get a page that can't exist (like page=42)"""

        self.client.force_login(self.profile1.user)

        response = self.client.get(
            reverse(
                "mp:view",
                kwargs={
                    "pk": self.topic1.pk,
                    "topic_slug": self.topic1.slug(),
                },
            )
            + "?page=42"
        )
        self.assertEqual(response.status_code, 404)

    def test_available_actions(self):
        """we should be able to cite, but not hide or alert"""

        self.client.force_login(self.profile1.user)

        response = self.client.get(
            reverse(
                "mp:view",
                kwargs={
                    "pk": self.topic1.pk,
                    "topic_slug": self.topic1.slug(),
                },
            )
        )

        # Citation button
        self.assertContains(response, "Citer")
        # no Alert button
        self.assertNotContains(response, "Signaler")
        # no Hide button
        self.assertNotContains(response, "Masquer")

    def test_more_than_one_message(self):
        """test get second page"""

        self.client.force_login(self.profile1.user)

        # create many subjects (at least two pages)
        post = None
        for i in range(1, settings.ZDS_APP["forum"]["topics_per_page"] + 5):
            post = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=i + 2)

        response = self.client.get(
            reverse(
                "mp:view",
                kwargs={
                    "pk": self.topic1.pk,
                    "topic_slug": self.topic1.slug(),
                },
            )
            + "?page=2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["posts"][-1], post)
        self.assertEqual(response.context["last_post_pk"], post.pk)


class NewTopicViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

        self.hat, _ = Hat.objects.get_or_create(name__iexact="A hat", defaults={"name": "A hat"})
        self.profile1.hats.add(self.hat)

        self.client.force_login(self.profile1.user)

    def test_denies_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse("mp:create"), follow=True)

        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("mp:create"))

    def test_success_get_with_and_without_username(self):
        response = self.client.get(reverse("mp:create"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.context["form"].initial["participants"], "")

        response2 = self.client.get(reverse("mp:create") + "?username=" + self.profile2.user.username)

        self.assertEqual(200, response2.status_code)
        self.assertEqual(self.profile2.user.username, response2.context["form"].initial["participants"])

    def test_success_get_with_multi_username(self):
        profile3 = ProfileFactory()

        response = self.client.get(
            reverse("mp:create") + "?username=" + self.profile2.user.username + "&username=" + profile3.user.username
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.context["form"].initial["participants"].split(", ")))
        self.assertTrue(self.profile1.user.username not in response.context["form"].initial["participants"])
        self.assertTrue(self.profile2.user.username in response.context["form"].initial["participants"])
        self.assertTrue(profile3.user.username in response.context["form"].initial["participants"])

    def test_success_get_with_and_without_title(self):
        response = self.client.get(reverse("mp:create"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.context["form"].initial["title"], "")

        response2 = self.client.get(reverse("mp:create") + "?title=Test titre")

        self.assertEqual(200, response2.status_code)
        self.assertEqual("Test titre", response2.context["form"].initial["title"])

    def test_fail_get_with_username_not_exist(self):
        response2 = self.client.get(reverse("mp:create") + "?username=wrongusername")

        self.assertEqual(200, response2.status_code)
        self.assertEqual(response2.context["form"].initial["participants"], "")

    def test_success_preview(self):
        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse("mp:create"),
            {
                "preview": "",
                "participants": self.profile2.user.username,
                "title": "title",
                "subtitle": "subtitle",
                "text": "text",
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_fail_new_topic_user_no_exist(self):
        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse("mp:create"),
            {"participants": "wronguser", "title": "title", "subtitle": "subtitle", "text": "text"},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_fail_new_topic_user_no_active(self):
        profile_inactive = ProfileFactory()
        profile_inactive.user.is_active = False
        profile_inactive.user.save()

        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse("mp:create"),
            {
                "participants": f"{profile_inactive.user.username}",
                "title": "title",
                "subtitle": "subtitle",
                "text": "text",
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_success_new_topic(self):
        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse("mp:create"),
            {"participants": self.profile2.user.username, "title": "title", "subtitle": "subtitle", "text": "text"},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.all().count())

    def test_new_topic_with_hat(self):
        response = self.client.post(
            reverse("mp:create"),
            {
                "participants": self.profile2.user.username,
                "title": "title",
                "subtitle": "subtitle",
                "text": "text",
                "with_hat": self.hat.pk,
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(PrivatePost.objects.latest("pubdate").hat, self.hat)

    def test_fail_new_topic_user_add_only_himself(self):
        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse("mp:create"),
            {"participants": self.profile1.user.username, "title": "title", "subtitle": "subtitle", "text": "text"},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_fail_new_topic_user_add_himself_and_others(self):
        self.assertEqual(0, PrivateTopic.objects.all().count())

        participants = self.profile2.user.username

        response = self.client.post(
            reverse("mp:create"),
            {"participants": participants, "title": "title", "subtitle": "subtitle", "text": "text"},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.all().count())
        self.assertNotIn(self.profile1.user, PrivateTopic.objects.all()[0].participants.all())


class AnswerViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()

        self.hat, _ = Hat.objects.get_or_create(name__iexact="A hat", defaults={"name": "A hat"})
        self.profile1.hats.add(self.hat)

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

        self.client.force_login(self.profile1.user)

    def test_denies_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse("mp:answer", args=[1, "private-topic"]), follow=True)

        self.assertRedirects(
            response, reverse("member-login") + "?next=" + reverse("mp:answer", args=[1, "private-topic"])
        )

    def test_fail_answer_not_send_topic_pk(self):
        response = self.client.post(reverse("mp:answer", args=[999, "private-topic"]))

        self.assertEqual(404, response.status_code)

    def test_fail_answer_topic_no_exist(self):
        response = self.client.post(reverse("mp:answer", args=[156, "private-topic"]))

        self.assertEqual(404, response.status_code)

    def test_fail_cite_post_no_exist(self):
        response = self.client.get(reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]) + "&cite=4864")

        self.assertEqual(404, response.status_code)

    def test_fail_cite_post_not_in_current_topic(self):
        another_topic = PrivateTopicFactory(author=self.profile2.user)
        another_post = PrivatePostFactory(privatetopic=another_topic, author=self.profile2.user, position_in_topic=1)

        response = self.client.get(
            reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]) + f"?cite={another_post.pk}"
        )

        self.assertEqual(403, response.status_code)

    def test_fail_cite_weird_pk(self):
        response = self.client.get(reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]) + "?cite=abcd")

        self.assertEqual(404, response.status_code)

    def test_success_cite_post(self):
        response = self.client.get(
            reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]) + f"?cite={self.post2.pk}"
        )

        self.assertEqual(200, response.status_code)

    def test_success_preview_answer(self):
        response = self.client.post(
            reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]),
            {"text": "answer", "preview": "", "last_post": self.topic1.last_message.pk},
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_success_answer(self):
        response = self.client.post(
            reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]),
            {"text": "Bonjour Luc", "last_post": self.topic1.last_message.pk},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, PrivatePost.objects.all().count())
        self.assertContains(response, "Bonjour Luc")

    def test_answer_with_hat(self):
        response = self.client.post(
            reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]),
            {
                "text": "Luc !?",
                "last_post": self.topic1.last_message.pk,
                "with_hat": self.hat.pk,
            },
            follow=False,
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual(PrivatePost.objects.latest("pubdate").hat, self.hat)

    def test_fail_answer_with_no_right(self):
        self.client.logout()
        self.client.force_login(self.profile3.user)

        response = self.client.post(
            reverse("mp:answer", args=[self.topic1.pk, self.topic1.slug()]),
            {"text": "answer", "last_post": self.topic1.last_message.pk},
            follow=True,
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(2, PrivatePost.objects.all().count())

    def test_unicode_title_answer(self):
        """To test unicode title."""

        unicode_topic = PrivateTopicFactory(author=self.profile1.user, title="Title with accent àéè")
        unicode_topic.participants.add(self.profile2.user)
        unicode_post = PrivatePostFactory(privatetopic=unicode_topic, author=self.profile1.user, position_in_topic=1)

        response = self.client.post(
            reverse("mp:answer", args=[unicode_topic.pk, unicode_topic.slug()]),
            {"text": "answer", "last_post": unicode_post.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_unicode_subtitle_answer(self):
        """To test unicode subtitle."""

        unicode_topic = PrivateTopicFactory(author=self.profile1.user, subtitle="Subtitle with accent àéè")
        unicode_topic.participants.add(self.profile2.user)
        unicode_post = PrivatePostFactory(privatetopic=unicode_topic, author=self.profile1.user, position_in_topic=1)

        response = self.client.post(
            reverse("mp:answer", args=[unicode_topic.pk, unicode_topic.slug()]),
            {"text": "answer", "last_post": unicode_post.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)


class EditPostViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

        self.client.force_login(self.profile1.user)

    def test_denies_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse("mp:post-edit", args=[1]), follow=True)

        self.assertRedirects(
            response,
            reverse("member-login") + "?next=" + reverse("mp:post-edit", args=[1]),
        )

    def test_succes_get_edit_post_page(self):
        self.client.logout()
        self.client.force_login(self.profile2.user)

        response = self.client.get(reverse("mp:post-edit", args=[self.post2.pk]))

        self.assertEqual(200, response.status_code)

    def test_fail_edit_post_no_exist(self):
        response = self.client.get(reverse("mp:post-edit", args=[154]))

        self.assertEqual(404, response.status_code)

    def test_fail_edit_post_not_last(self):
        response = self.client.get(reverse("mp:post-edit", args=[self.post1.pk]))

        self.assertEqual(403, response.status_code)

    def test_fail_edit_post_with_no_right(self):
        response = self.client.get(reverse("mp:post-edit", args=[self.post2.pk]))

        self.assertEqual(403, response.status_code)

    def test_success_edit_post(self):
        self.client.logout()
        self.client.force_login(self.profile2.user)

        response = self.client.post(
            reverse("mp:post-edit", args=[self.post2.pk]),
            {
                "text": "update post",
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("update post", PrivatePost.objects.get(pk=self.post2.pk).text)

    def test_text_absent(self):
        """test what happens if the text is not sent"""

        response = self.client.post(
            reverse("mp:post-edit", args=[self.post2.pk]),
            {
                "text": "",
            },
            follow=True,
        )
        self.assertEqual(403, response.status_code)

    def test_preview_no_text(self):
        """test what happens when we preview with no text"""

        response = self.client.post(
            reverse("mp:post-edit", args=[self.post2.pk]),
            {
                "preview": "",
            },
            follow=True,
        )
        self.assertEqual(403, response.status_code)
        # 403 because resend the same view without the preview parameter


class LeaveViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()

        self.anonymous_account = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"])
        self.bot_group = Group()
        self.bot_group.name = settings.ZDS_APP["member"]["bot_group"]
        self.bot_group.save()
        self.anonymous_account.groups.add(self.bot_group)
        self.anonymous_account.save()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

        self.client.force_login(self.profile1.user)

    def test_denies_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse("mp:leave", args=[1, "private-topic"]), follow=True)

        self.assertRedirects(
            response, reverse("member-login") + "?next=" + reverse("mp:leave", args=[1, "private-topic"])
        )

    def test_denies_leave_topic_as_random_member(self):
        self.client.force_login(self.profile3.user)

        response = self.client.post(reverse("mp:leave", args=[self.topic1.pk, self.topic1.slug()]), follow=True)

        self.assertEqual(403, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.filter(pk=self.topic1.pk).count())

    def test_fail_leave_topic_no_exist(self):
        response = self.client.post(reverse("mp:leave", args=[999, "private-topic"]))

        self.assertEqual(404, response.status_code)

    def test_success_leave_topic_as_author_no_participants(self):
        self.topic1.participants.clear()
        self.topic1.save()

        response = self.client.post(reverse("mp:leave", args=[self.topic1.pk, self.topic1.slug()]), follow=True)

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=self.topic1.pk).all().count())

    def test_success_leave_topic_as_author(self):
        response = self.client.post(reverse("mp:leave", args=[self.topic1.pk, self.topic1.slug()]), follow=True)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.filter(pk=self.topic1.pk).all().count())

        self.assertEqual(self.profile2.user, PrivateTopic.objects.get(pk=self.topic1.pk).author)

    def test_success_leave_topic_as_participant(self):
        self.client.logout()
        self.client.force_login(self.profile2.user)

        response = self.client.post(reverse("mp:leave", args=[self.topic1.pk, self.topic1.slug()]), follow=True)

        self.assertEqual(200, response.status_code)

        self.assertNotIn(self.profile2.user, PrivateTopic.objects.get(pk=self.topic1.pk).participants.all())

        self.assertNotEqual(self.profile2.user, PrivateTopic.objects.get(pk=self.topic1.pk).author)


class AddParticipantViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.anonymous_account = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"])
        self.bot_group = Group()
        self.bot_group.name = settings.ZDS_APP["member"]["bot_group"]
        self.bot_group.save()
        self.anonymous_account.groups.add(self.bot_group)
        self.anonymous_account.save()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

        self.client.force_login(self.profile1.user)

    def test_denies_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse("mp:edit-participant", args=[1, "private-topic"]), follow=True)

        self.assertRedirects(
            response, reverse("member-login") + "?next=" + reverse("mp:edit-participant", args=[1, "private-topic"])
        )

    def test_fail_add_participant_topic_no_exist(self):
        response = self.client.post(reverse("mp:edit-participant", args=[451, "private-topic"]), follow=True)

        self.assertEqual(404, response.status_code)

    def test_test_fail_add_bot_as_participant(self):
        self.client.logout()
        self.client.force_login(self.profile1.user)

        self.client.post(
            reverse("mp:edit-participant", args=[self.topic1.pk, self.topic1.slug()]),
            {"username": self.anonymous_account.username},
        )

        # TODO (Arnaud-D): this test actually succeeds because of a Http404.
        #  NotReachableError is not raised.
        self.assertFalse(self.anonymous_account in self.topic1.participants.all())

    def test_fail_add_participant_who_no_exist(self):
        response = self.client.post(
            reverse("mp:edit-participant", args=[self.topic1.pk, self.topic1.slug()]),
            {"username": "178548"},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["messages"]))

    def test_fail_add_participant_with_no_right(self):
        profile3 = ProfileFactory()

        self.client.logout()
        self.client.force_login(profile3.user)

        response = self.client.post(
            reverse("mp:edit-participant", args=[self.topic1.pk, self.topic1.slug()]),
            {"username": profile3.user.username},
        )

        self.assertEqual(403, response.status_code)
        self.assertNotIn(profile3.user, PrivateTopic.objects.get(pk=self.topic1.pk).participants.all())

    def test_fail_add_participant_already_in(self):
        response = self.client.post(
            reverse("mp:edit-participant", args=[self.topic1.pk, self.topic1.slug()]),
            {"username": self.profile2.user.username},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["messages"]))

    def test_success_add_participant(self):
        profile3 = ProfileFactory()

        response = self.client.post(
            reverse("mp:edit-participant", args=[self.topic1.pk, self.topic1.slug()]),
            {"username": profile3.user.username},
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["messages"]))
        self.assertIn(profile3.user, PrivateTopic.objects.get(pk=self.topic1.pk).participants.all())


class PrivateTopicEditTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile1.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.profile2.user, position_in_topic=2)

    def test_denies_anonymous(self):
        self.client.logout()
        self.topic1.title = "super title"
        self.topic1.subtitle = "super subtitle"
        self.topic1.save()

        # get
        response = self.client.get(reverse("mp:edit", args=[self.topic1.pk, "private-topic"]), follow=True)

        self.assertRedirects(
            response,
            reverse("member-login") + "?next=" + reverse("mp:edit", args=[self.topic1.pk, "private-topic"]),
        )

        # post
        response = self.client.post(
            reverse("mp:edit", args=[self.topic1.pk, "private-topic"]),
            {"title": "test", "subtitle": "subtest"},
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("member-login") + "?next=" + reverse("mp:edit", args=[self.topic1.pk, "private-topic"]),
        )

        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertEqual("super title", topic.title)
        self.assertEqual("super subtitle", topic.subtitle)

    def test_success_edit_topic(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("mp:edit", args=[self.topic1.pk, "private-topic"]),
            {"title": "test", "subtitle": "subtest"},
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertEqual("test", topic.title)
        self.assertEqual("subtest", topic.subtitle)

    def test_fail_user_is_not_author(self):
        self.topic1.title = "super title"
        self.topic1.subtitle = "super subtitle"
        self.topic1.save()

        self.client.force_login(self.profile2.user)

        response = self.client.get(reverse("mp:edit", args=[self.topic1.pk, "private-topic"]), follow=True)
        self.assertEqual(403, response.status_code)

        response = self.client.post(
            reverse("mp:edit", args=[self.topic1.pk, "private-topic"]),
            {"title": "test", "subtitle": "subtest"},
            follow=True,
        )

        self.assertEqual(403, response.status_code)

        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertEqual("super title", topic.title)
        self.assertEqual("super subtitle", topic.subtitle)

    def test_fail_topic_doesnt_exist(self):
        self.client.force_login(self.profile1.user)

        response = self.client.get(reverse("mp:edit", args=[91, "private-topic"]), follow=True)
        self.assertEqual(404, response.status_code)

        response = self.client.post(
            reverse("mp:edit", args=[91, "private-topic"]),
            {"title": "test", "subtitle": "subtest"},
            follow=True,
        )
        self.assertEqual(404, response.status_code)

    def test_fail_blank_title(self):
        self.topic1.title = "super title"
        self.topic1.subtitle = "super subtitle"
        self.topic1.save()

        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("mp:edit", args=[self.topic1.pk, "private-topic"]),
            {"title": "", "subtitle": "subtest"},
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertEqual("super title", topic.title)
        self.assertEqual("super subtitle", topic.subtitle)


class PrivatePostUnreadTest(TestCase):
    def setUp(self):
        self.author = ProfileFactory()
        self.participant = ProfileFactory()
        self.outsider = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.author.user)
        self.topic1.participants.add(self.participant.user)
        self.post1 = PrivatePostFactory(privatetopic=self.topic1, author=self.author.user, position_in_topic=1)

        self.post2 = PrivatePostFactory(privatetopic=self.topic1, author=self.participant.user, position_in_topic=2)

    def test_denies_anonymous(self):
        """Test the case of an unauthenticated user trying to unread a private post."""
        self.client.logout()
        response = self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post2.pk}), follow=True)

        self.assertRedirects(
            response,
            reverse("member-login") + "?next=" + reverse("mp:mark-post-unread", kwargs={"pk": self.post2.pk}),
        )

    def test_failing_unread_post(self):
        """Test cases of invalid unread requests by an authenticated user."""
        self.client.force_login(self.author.user)
        # parameter doesn't (yet) exist
        result = self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": 424242}), follow=False)
        self.assertEqual(result.status_code, 404)

    def test_user_not_participating(self):
        """Test the case of a user not participating in a private topic attempting to unread a post."""
        self.client.force_login(self.outsider.user)
        result = self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post2.pk}), follow=False)
        self.assertEqual(result.status_code, 403)

    @patch("zds.mp.signals.message_unread")
    def test_unread_first_post(self, message_unread):
        self.client.force_login(self.participant.user)
        result = self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post1.pk}), follow=True)
        self.assertRedirects(result, reverse("mp:list"))
        with self.assertRaises(PrivateTopicRead.DoesNotExist):
            PrivateTopicRead.objects.get(privatetopic=self.post1.privatetopic, user=self.participant.user)
        self.assertEqual(message_unread.send.call_count, 1)

    @patch("zds.mp.signals.message_unread")
    def test_unread_normal_post(self, message_unread):
        self.client.force_login(self.participant.user)
        self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post2.pk}), follow=True)
        topic_read = PrivateTopicRead.objects.get(privatetopic=self.post2.privatetopic, user=self.participant.user)
        self.assertEqual(topic_read.privatetopic, self.topic1)
        self.assertEqual(topic_read.user, self.participant.user)
        self.assertEqual(topic_read.privatepost, self.post1)
        self.assertEqual(message_unread.send.call_count, 1)

    @patch("zds.mp.signals.message_unread")
    def test_multiple_unread1(self, message_unread):
        self.client.force_login(self.participant.user)
        self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post1.pk}), follow=True)
        self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post2.pk}), follow=True)
        topic_read = PrivateTopicRead.objects.get(privatetopic=self.post2.privatetopic, user=self.participant.user)
        self.assertEqual(topic_read.privatetopic, self.topic1)
        self.assertEqual(topic_read.user, self.participant.user)
        self.assertEqual(topic_read.privatepost, self.post1)
        self.assertEqual(message_unread.send.call_count, 2)

    @patch("zds.mp.signals.message_unread")
    def test_multiple_unread2(self, message_unread):
        self.client.force_login(self.participant.user)
        for _ in range(2):
            self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post1.pk}), follow=True)
        with self.assertRaises(PrivateTopicRead.DoesNotExist):
            PrivateTopicRead.objects.get(privatetopic=self.post1.privatetopic, user=self.participant.user)
        self.assertEqual(message_unread.send.call_count, 2)

    def test_no_interference(self):
        mark_read(self.topic1, self.author.user)
        topic_read_old = PrivateTopicRead.objects.filter(privatetopic=self.topic1, user=self.author.user)
        self.client.force_login(self.participant.user)
        self.client.get(reverse("mp:mark-post-unread", kwargs={"pk": self.post2.pk}), follow=True)
        topic_read_new = PrivateTopicRead.objects.filter(privatetopic=self.topic1, user=self.author.user)
        self.assertQuerysetEqual(topic_read_old, topic_read_new)
