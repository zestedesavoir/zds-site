import datetime
from copy import deepcopy
import os
import shutil

from django.conf import settings
from django.core.cache import caches
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.member.factories import ProfileFactory
from zds.tutorialv2.factories import ContentReactionFactory, PublishedContentFactory
from zds.utils.models import CommentVote

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')
overridden_zds_app['content']['extra_content_generation_policy'] = 'SYNC'
overridden_zds_app['content']['build_pdf_when_published'] = False


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
class ContentReactionKarmaAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()
        self.content = PublishedContentFactory()
        self.content.save()

    def test_failure_reaction_karma_with_client_unauthenticated(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content,
                                          pubdate=datetime.datetime.now())

        response = self.client.put(reverse('api:content:reaction-karma', args=(reaction.pk,)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_failure_reaction_karma_with_sanctioned_user(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:content:reaction-karma', args=(reaction.pk,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_reaction_karma_with_a_message_not_found(self):
        response = self.client.get(reverse('api:content:reaction-karma', args=(99999,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_success_reaction_karma_like(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:content:reaction-karma', args=(reaction.pk,)), {'vote': 'like'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=reaction, positive=True).exists())

    def test_success_reaction_karma_dislike(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:content:reaction-karma', args=(reaction.pk,)), {'vote': 'dislike'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=reaction, positive=False).exists())

    def test_success_reaction_karma_neutral(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()

        vote = CommentVote(user=profile.user, comment=reaction, positive=True)
        vote.save()

        self.assertTrue(CommentVote.objects.filter(pk=vote.pk).exists())
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:content:reaction-karma', args=(reaction.pk,)), {'vote': 'neutral'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk).exists())

    def test_success_reaction_karma_like_already_disliked(self):
        author = ProfileFactory()
        reaction = ContentReactionFactory(author=author.user, position=1, related_content=self.content)

        profile = ProfileFactory()

        vote = CommentVote(user=profile.user, comment=reaction, positive=False)
        vote.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:content:reaction-karma', args=(reaction.pk,)), {'vote': 'like'})
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

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))

        # on first message we should see 2 likes and 0 anonymous
        response = self.client.get(reverse('api:content:reaction-karma', args=[upvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data['like']['users']))
        self.assertEqual(0, len(response.data['dislike']['users']))
        self.assertEqual(2, response.data['like']['count'])
        self.assertEqual(0, response.data['dislike']['count'])

        # on second message we should see 2 dislikes and 0 anonymous
        response = self.client.get(reverse('api:content:reaction-karma', args=[downvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data['like']['users']))
        self.assertEqual(2, len(response.data['dislike']['users']))
        self.assertEqual(0, response.data['like']['count'])
        self.assertEqual(2, response.data['dislike']['count'])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse('api:content:reaction-karma', args=[equal_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['like']['users']))
        self.assertEqual(1, len(response.data['dislike']['users']))
        self.assertEqual(1, response.data['like']['count'])
        self.assertEqual(1, response.data['dislike']['count'])

        # Now we change the settings to keep anonymous the first [dis]like
        settings.VOTES_ID_LIMIT = anon_limit.pk
        # and we run the same tests
        # on first message we should see 1 like and 1 anonymous
        response = self.client.get(reverse('api:content:reaction-karma', args=[upvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['like']['users']))
        self.assertEqual(0, len(response.data['dislike']['users']))
        self.assertEqual(2, response.data['like']['count'])
        self.assertEqual(0, response.data['dislike']['count'])

        # on second message we should see 1 dislikes and 1 anonymous
        response = self.client.get(reverse('api:content:reaction-karma', args=[downvoted_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data['like']['users']))
        self.assertEqual(1, len(response.data['dislike']['users']))
        self.assertEqual(0, response.data['like']['count'])
        self.assertEqual(2, response.data['dislike']['count'])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse('api:content:reaction-karma', args=[equal_reaction.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['like']['users']))
        self.assertEqual(1, len(response.data['dislike']['users']))
        self.assertEqual(1, response.data['like']['count'])
        self.assertEqual(1, response.data['dislike']['count'])
