import datetime
import os
import shutil

from django.conf import settings
from django.core.cache import caches
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublicationEvent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ContentReactionFactory, PublishedContentFactory
from zds.utils.models import CommentVote


@override_for_contents()
class ContentReactionKarmaAPITest(TutorialTestMixin, APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()
        self.content = PublishedContentFactory()
        self.content.save()

    def test_failure_reaction_karma_with_client_unauthenticated(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(
            author=author.user, position=1, related_content=self.content, pubdate=datetime.datetime.now()
        )

        response = self.client.put(reverse("api:content:reaction-karma", args=(reaction.pk,)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP["content"]["repo_private_path"]):
            shutil.rmtree(settings.ZDS_APP["content"]["repo_private_path"])
        if os.path.isdir(settings.ZDS_APP["content"]["repo_public_path"]):
            shutil.rmtree(settings.ZDS_APP["content"]["repo_public_path"])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_failure_reaction_karma_with_sanctioned_user(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:content:reaction-karma", args=(reaction.pk,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_reaction_karma_with_a_message_not_found(self):
        response = self.client.get(reverse("api:content:reaction-karma", args=(99999,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_success_reaction_karma_like(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:content:reaction-karma", args=(reaction.pk,)), {"vote": "like"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=reaction, positive=True).exists())

    def test_success_reaction_karma_dislike(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:content:reaction-karma", args=(reaction.pk,)), {"vote": "dislike"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=reaction, positive=False).exists())

    def test_success_reaction_karma_neutral(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()

        vote = CommentVote(user=profile.user, comment=reaction, positive=True)
        vote.save()

        self.assertTrue(CommentVote.objects.filter(pk=vote.pk).exists())
        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:content:reaction-karma", args=(reaction.pk,)), {"vote": "neutral"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk).exists())

    def test_success_reaction_karma_like_already_disliked(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()

        vote = CommentVote(user=profile.user, comment=reaction, positive=False)
        vote.save()

        self.client.force_login(profile.user)
        response = self.client.put(reverse("api:content:reaction-karma", args=(reaction.pk,)), {"vote": "like"})
        vote.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(vote.positive)

    def test_get_content_reaction_voters(self):
        author = ProfileFactory()
        profile = ProfileFactory()
        profile2 = ProfileFactory()

        upvoted_reaction = ContentReactionFactory(author=author.user, position=2, related_content=self.content)
        upvoted_reaction.like += 2
        upvoted_reaction.save()
        CommentVote.objects.create(user=profile.user, comment=upvoted_reaction, positive=True)

        downvoted_reaction = ContentReactionFactory(author=author.user, position=3, related_content=self.content)
        downvoted_reaction.dislike += 2
        downvoted_reaction.save()
        anon_limit = CommentVote.objects.create(user=profile.user, comment=downvoted_reaction, positive=False)

        CommentVote.objects.create(user=profile2.user, comment=upvoted_reaction, positive=True)
        CommentVote.objects.create(user=profile2.user, comment=downvoted_reaction, positive=False)

        equal_reaction = ContentReactionFactory(author=author.user, position=4, related_content=self.content)
        equal_reaction.like += 1
        equal_reaction.dislike += 1
        equal_reaction.save()

        CommentVote.objects.create(user=profile.user, comment=equal_reaction, positive=True)
        CommentVote.objects.create(user=profile2.user, comment=equal_reaction, positive=False)

        self.client.force_login(profile.user)

        # on first message we should see 2 likes and 0 anonymous
        response = self.client.get(reverse("api:content:reaction-karma", args=[upvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data["like"]["users"]))
        self.assertEqual(0, len(response.data["dislike"]["users"]))
        self.assertEqual(2, response.data["like"]["count"])
        self.assertEqual(0, response.data["dislike"]["count"])

        # on second message we should see 2 dislikes and 0 anonymous
        response = self.client.get(reverse("api:content:reaction-karma", args=[downvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data["like"]["users"]))
        self.assertEqual(2, len(response.data["dislike"]["users"]))
        self.assertEqual(0, response.data["like"]["count"])
        self.assertEqual(2, response.data["dislike"]["count"])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse("api:content:reaction-karma", args=[equal_reaction.pk]))
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
        response = self.client.get(reverse("api:content:reaction-karma", args=[upvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data["like"]["users"]))
        self.assertEqual(0, len(response.data["dislike"]["users"]))
        self.assertEqual(2, response.data["like"]["count"])
        self.assertEqual(0, response.data["dislike"]["count"])

        # on second message we should see 1 dislikes and 1 anonymous
        response = self.client.get(reverse("api:content:reaction-karma", args=[downvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data["like"]["users"]))
        self.assertEqual(1, len(response.data["dislike"]["users"]))
        self.assertEqual(0, response.data["like"]["count"])
        self.assertEqual(2, response.data["dislike"]["count"])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse("api:content:reaction-karma", args=[equal_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data["like"]["users"]))
        self.assertEqual(1, len(response.data["dislike"]["users"]))
        self.assertEqual(1, response.data["like"]["count"])
        self.assertEqual(1, response.data["dislike"]["count"])
        settings.VOTES_ID_LIMIT = previous_limit


@override_for_contents()
class ContentExportsAPITest(TutorialTestMixin, APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP["content"]["repo_private_path"]):
            shutil.rmtree(settings.ZDS_APP["content"]["repo_private_path"])
        if os.path.isdir(settings.ZDS_APP["content"]["repo_public_path"]):
            shutil.rmtree(settings.ZDS_APP["content"]["repo_public_path"])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_request_content_exports_generation(self):
        author = ProfileFactory()
        not_author = ProfileFactory()
        staff = StaffProfileFactory()

        content = PublishedContentFactory(author_list=[author.user]).public_version

        self.assertEqual(0, PublicationEvent.objects.filter(published_object=content).count())

        # Anonymous sender should not be able to ask for exports generation
        response = self.client.post(reverse("api:content:generate_export", args=[content.content.pk]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(0, PublicationEvent.objects.filter(published_object=content).count())

        # An authenticated author but not an author should not either
        self.client.force_login(not_author.user)
        response = self.client.post(reverse("api:content:generate_export", args=[content.content.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(0, PublicationEvent.objects.filter(published_object=content).count())

        # But if the user is staff, it should
        self.client.force_login(staff.user)
        response = self.client.post(reverse("api:content:generate_export", args=[content.content.pk]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        requests_count = PublicationEvent.objects.filter(published_object=content).count()
        self.assertGreater(requests_count, 0)

        # And if the user is an author, it should too
        self.client.force_login(author.user)
        response = self.client.post(reverse("api:content:generate_export", args=[content.content.pk]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # And it should be equal than the previous one as we added new request,
        # but the watchdog wasn't launched to handle them:
        self.assertEqual(PublicationEvent.objects.filter(published_object=content).count(), requests_count)

        self.client.logout()

    def test_content_exports_list(self):
        author = ProfileFactory()
        content = PublishedContentFactory(author_list=[author.user]).public_version

        # Anonymous usage should be allowed
        # We check that no extraneous SQL query is executed, as this API‌ is used
        # for live updates.
        # Here we expect one request, as there are no records. For other calls,
        # we expect two requests: one for the exports list and one for the
        # PublishedContent prefetch (to get the export's URL).
        with self.assertNumQueries(1):
            response = self.client.get(reverse("api:content:list_exports", args=[content.content.pk]), type="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # At this point, no export was generated so this should be empty
            self.assertEqual(response.data, [])

        # Let's request some
        self.client.force_login(author.user)
        response = self.client.post(reverse("api:content:generate_export", args=[content.content.pk]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        requests_count = PublicationEvent.objects.filter(published_object=content).count()

        self.client.logout()

        with self.assertNumQueries(2):
            response = self.client.get(reverse("api:content:list_exports", args=[content.content.pk]), type="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), requests_count)

        # Let's request some more. The API should only return the latest ones, so
        # even if there are some more records in the database, the count should stay
        # the same.
        self.client.force_login(author.user)
        response = self.client.post(reverse("api:content:generate_export", args=[content.content.pk]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()

        with self.assertNumQueries(2):
            response = self.client.get(reverse("api:content:list_exports", args=[content.content.pk]), type="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), requests_count)

        # We create another content. Even if there are some records in the database,
        # they should not be returned for this new content.
        other_content = PublishedContentFactory(author_list=[author.user])

        # One request as there are no export: no prefetch needed.
        with self.assertNumQueries(1):
            response = self.client.get(reverse("api:content:list_exports", args=[other_content.pk]), type="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, [])
