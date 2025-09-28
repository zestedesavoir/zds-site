from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.forum.tests.factories import PostFactory, create_category_and_forum, create_topic_in_forum
from zds.member.tests.factories import ProfileFactory
from zds.utils.models import CommentVote


class ForumPostKarmaAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_failure_post_karma_with_client_unauthenticated(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=2)

        response = self.client.put(reverse("api:forum:post-karma", args=(post.pk,)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_failure_post_karma_with_sanctioned_user(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:forum:post-karma", args=(post.pk,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_post_karma_with_a_message_not_found(self):
        response = self.client.get(reverse("api:forum:post-karma", args=(99999,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_failure_post_karma_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category, forum = create_category_and_forum(group)
        topic = create_topic_in_forum(forum, profile)

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:forum:post-karma", args=(topic.last_message.pk,)), {"vote": "like"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success_post_karma_like(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:forum:post-karma", args=(post.pk,)), {"vote": "like"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=post, positive=True).exists())

    def test_success_post_karma_dislike(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:forum:post-karma", args=(post.pk,)), {"vote": "dislike"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=post, positive=False).exists())

    def test_success_post_karma_neutral(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        vote = CommentVote(user=profile.user, comment=post, positive=True)
        vote.save()

        self.assertTrue(CommentVote.objects.filter(pk=vote.pk).exists())
        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:forum:post-karma", args=(post.pk,)), {"vote": "neutral"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk).exists())

    def test_success_post_karma_like_already_disliked(self):
        profile = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        vote = CommentVote(user=profile.user, comment=post, positive=False)
        vote.save()

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:forum:post-karma", args=(post.pk,)), {"vote": "like"})
        vote.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(vote.positive)

    def test_get_post_voters(self):
        profile = ProfileFactory()
        profile2 = ProfileFactory()
        category, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        another_profile = ProfileFactory()

        upvoted_answer = PostFactory(topic=topic, author=another_profile.user, position=2)
        upvoted_answer.like += 2
        upvoted_answer.save()
        CommentVote.objects.create(user=profile.user, comment=upvoted_answer, positive=True)

        downvoted_answer = PostFactory(topic=topic, author=another_profile.user, position=3)
        downvoted_answer.dislike += 2
        downvoted_answer.save()
        anon_limit = CommentVote.objects.create(user=profile.user, comment=downvoted_answer, positive=False)

        CommentVote.objects.create(user=profile2.user, comment=upvoted_answer, positive=True)
        CommentVote.objects.create(user=profile2.user, comment=downvoted_answer, positive=False)

        equal_answer = PostFactory(topic=topic, author=another_profile.user, position=4)
        equal_answer.like += 1
        equal_answer.dislike += 1
        equal_answer.save()
        CommentVote.objects.create(user=profile.user, comment=equal_answer, positive=True)
        CommentVote.objects.create(user=profile2.user, comment=equal_answer, positive=False)

        self.client.force_login(profile.user)

        # on first message we should see 2 likes and 0 anonymous
        response = self.client.get(reverse("api:forum:post-karma", args=[upvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data["like"]["users"]))
        self.assertEqual(0, len(response.data["dislike"]["users"]))
        self.assertEqual(2, response.data["like"]["count"])
        self.assertEqual(0, response.data["dislike"]["count"])

        # on second message we should see 2 dislikes and 0 anonymous
        response = self.client.get(reverse("api:forum:post-karma", args=[downvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data["like"]["users"]))
        self.assertEqual(2, len(response.data["dislike"]["users"]))
        self.assertEqual(0, response.data["like"]["count"])
        self.assertEqual(2, response.data["dislike"]["count"])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse("api:forum:post-karma", args=[equal_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data["like"]["users"]))
        self.assertEqual(1, len(response.data["dislike"]["users"]))
        self.assertEqual(1, response.data["like"]["count"])
        self.assertEqual(1, response.data["dislike"]["count"])

        # Now we change the settings to keep anonymous the first [dis]like
        previous_limit = settings.VOTES_ID_LIMIT
        settings.VOTES_ID_LIMIT = anon_limit.pk
        # and we run the same tests
        # on first message we should see 1 like and 1 anonymous
        response = self.client.get(reverse("api:forum:post-karma", args=[upvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data["like"]["users"]))
        self.assertEqual(0, len(response.data["dislike"]["users"]))
        self.assertEqual(2, response.data["like"]["count"])
        self.assertEqual(0, response.data["dislike"]["count"])

        # on second message we should see 1 dislikes and 1 anonymous
        response = self.client.get(reverse("api:forum:post-karma", args=[downvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data["like"]["users"]))
        self.assertEqual(1, len(response.data["dislike"]["users"]))
        self.assertEqual(0, response.data["like"]["count"])
        self.assertEqual(2, response.data["dislike"]["count"])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse("api:forum:post-karma", args=[equal_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data["like"]["users"]))
        self.assertEqual(1, len(response.data["dislike"]["users"]))
        self.assertEqual(1, response.data["like"]["count"])
        self.assertEqual(1, response.data["dislike"]["count"])

        settings.VOTES_ID_LIMIT = previous_limit
