import datetime
import os
import shutil

from django.conf import settings
from django.core.cache import caches
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.member.api.tests import create_oauth2_client, authenticate_client
from zds.member.factories import ProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.api.serializers import ChildrenListModifySerializer
from zds.tutorialv2.api.view_models import UpdateChildrenListViewModel
from zds.tutorialv2.factories import ContentReactionFactory, PublishedContentFactory, PublishableContentFactory
from zds.tutorialv2.models.database import PublishableContent
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


class TestChildrenListSerializer(TestCase):
    def test_good_input(self):
        data = {
            'containers': [],
            'extracts': [
                {'title': 'Sit minus molestias omnis dolorum et tempora.',
                 'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                 'child_type': 'extract', 'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'},
                {'title': 'un titre au milieu', 'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                 'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
            ],
            'introduction': 'Ceci est un texte bidon, **avec markown**',
            'conclusion': 'Ceci est un texte bidon, **avec markown**',
            'remove_deleted_children': True, 'message': 'edition',
            'original_sha': 'd33fef58bedd39dc1c2d38f16305b10010e9058e'}
        serializer = ChildrenListModifySerializer(data=data,
                                                  db_object=PublishableContent(sha_draft='d33fef58bedd39dc1c2'
                                                                                         'd38f16305b10010e9058e'))
        self.assertTrue(serializer.is_valid())
        self.assertIsInstance(serializer.create(serializer.validated_data), UpdateChildrenListViewModel)

    def test_missing_not_optional_parameters(self):
        data = {
            'containers': [],
            'extracts': [
                {'title': 'Sit minus molestias omnis dolorum et tempora.',
                 'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                 'child_type': 'extract', 'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'},
                {'title': 'un titre au milieu', 'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                 'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
            ], 'original_sha': 'd33fef58bedd39dc1c2d38f16305b10010e9058e'}
        serializer = ChildrenListModifySerializer(data=data,
                                                  db_object=PublishableContent(sha_draft='d33fef58bedd39dc1c2'
                                                                                         'd38f16305b10010e9058e'))
        self.assertTrue(serializer.is_valid())
        created = serializer.create(serializer.validated_data)
        self.assertIsInstance(created, UpdateChildrenListViewModel)
        self.assertIsNotNone(created.introduction)
        self.assertIsNotNone(created.conclusion)
        self.assertIsNotNone(created.message)
        self.assertFalse(created.remove_deleted_children)

    def test_bad_extract_type(self):
        data = {
            'containers': [],
            'extracts': [
                {'title': 'Sit minus molestias omnis dolorum et tempora.',
                 'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                 'child_type': 'extracts', 'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'},
                {'title': 'un titre au milieu', 'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                 'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
            ], 'original_sha': 'd33fef58bedd39dc1c2d38f16305b10010e9058e'}
        serializer = ChildrenListModifySerializer(data=data,
                                                  db_object=PublishableContent(sha_draft='d33fef58bedd39dc1c2'
                                                                                         'd38f16305b10010e9058e'))
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)

    def test_bad_extract_format(self):
        data = {
            'containers': [],
            'extracts': [
                {'title': 'Sit minus molestias omnis dolorum et tempora.',
                 'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                 'child_type': 'extract', 'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora',
                 'description': 'this is a description, extracts has no description'},
                {'title': 'un titre au milieu', 'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                 'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
            ],
            'introduction': 'Ceci est un texte bidon, **avec markown**',
            'conclusion': 'Ceci est un texte bidon, **avec markown**',
            'remove_deleted_children': True, 'message': 'edition',
            'original_sha': 'd33fef58bedd39dc1c2d38f16305b10010e9058e'}
        serializer = ChildrenListModifySerializer(data=data,
                                                  db_object=PublishableContent(sha_draft='d33fef58bedd39dc1c2'
                                                                                         'd38f16305b10010e9058e'))
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)


class ContentAPIChildrenUpdate(TutorialTestMixin, APITestCase):
    def setUp(self):
        self.author = ProfileFactory().user
        self.client_user = ProfileFactory()

        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()
        self.client_oauth2 = create_oauth2_client(self.client_user.user)
        self.content = PublishableContentFactory(author_list=[self.author])
        self.content.save()

    def test_add_extract(self):
        authenticate_client(self.client, self.client_oauth2, self.author.username, 'hostel77')
        resp = self.client.put(reverse('api:content:children-content', args=[self.content.pk, self.content.slug]),
                               data={
                                   'original_sha': self.content.sha_draft,
                                   'containers': [],
                                   'extracts': [
                                       {'title': 'Sit minus molestias omnis dolorum et tempora.',
                                        'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                                        'child_type': 'extract',
                                        'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'},
                                       {'title': 'un titre au milieu',
                                        'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                                        'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
                                   ],
                                   'introduction': 'Ceci est un texte bidon, **avec markown**',
                                   'conclusion': 'Ceci est un texte bidon, **avec markown**',
                                   'remove_deleted_children': True, 'message': 'edition'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        self.assertNotEqual(self.content.sha_draft, PublishableContent.objects.get(pk=self.content.pk).sha_draft)

    def test_forbidden_access(self):
        authenticate_client(self.client, self.client_oauth2, self.client_user.user.username, 'hostel77')
        resp = self.client.put(reverse('api:content:children-content', args=[self.content.pk, self.content.slug]),
                               data={
                                   'original_sha': self.content.sha_draft,
                                   'containers': [],
                                   'extracts': [{
                                       'title': 'Sit minus molestias omnis dolorum et tempora.',
                                       'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                                       'child_type': 'extract',
                                       'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'
                                   }, {
                                       'title': 'un titre au milieu',
                                       'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                                       'child_type': 'extract', 'slug': 'un-titre-au-milieu'
                                   }
                                   ],
                                   'introduction': 'Ceci est un texte bidon, **avec markown**',
                                   'conclusion': 'Ceci est un texte bidon, **avec markown**',
                                   'remove_deleted_children': True, 'message': 'edition'}
                               )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_insert_new_extract(self):
        authenticate_client(self.client, self.client_oauth2, self.author.username, 'hostel77')
        resp = self.client.put(reverse('api:content:children-content', args=[self.content.pk, self.content.slug]),
                               data={
                                   'original_sha': self.content.sha_draft,
                                   'containers': [],
                                   'extracts': [
                                       {'title': 'Sit minus molestias omnis dolorum et tempora.',
                                        'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                                        'child_type': 'extract',
                                        'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'},
                                       {'title': 'un titre au milieu',
                                        'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                                        'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
                                   ],
                                   'introduction': 'Ceci est un texte bidon, **avec markown**',
                                   'conclusion': 'Ceci est un texte bidon, **avec markown**',
                                   'remove_deleted_children': True, 'message': 'edition'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        saved = PublishableContent.objects.get(pk=self.content.pk)
        self.assertNotEqual(self.content.sha_draft, saved.sha_draft)
        resp = self.client.put(reverse('api:content:children-content', args=[self.content.pk, self.content.slug]),
                               data={
                                   'original_sha': saved.sha_draft,
                                   'containers': [],
                                   'extracts': [
                                       {'title': 'Sit minus molestias omnis dolorum et tempora.',
                                        'text': "Ceci est un texte contenant plein d'images, pour la publication.",
                                        'child_type': 'extract',
                                        'slug': 'sit-minus-molestias-omnis-dolorum-et-tempora'},
                                       {'title': 'un titre au inséré',
                                        'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                                        'child_type': 'extract', 'slug': 'un-titre-insere'},
                                       {'title': 'un titre au milieu',
                                        'text': 'blabla bla\n\n# Et donc ...\n\nVoilà :)',
                                        'child_type': 'extract', 'slug': 'un-titre-au-milieu'}
                                   ],
                                   'introduction': 'Ceci est un texte bidon, **avec markown**',
                                   'conclusion': 'Ceci est un texte bidon, **avec markown**',
                                   'remove_deleted_children': True, 'message': 'edition'})
        new_version = PublishableContent.objects.get(pk=self.content.pk)
        self.assertNotEqual(new_version.sha_draft, saved.sha_draft)
        self.assertEqual(3, len(new_version.load_version().children))
        self.assertEqual('un-titre-insere', new_version.load_version().children[1].slug)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        # re-active PDF build
        settings.ZDS_APP['content']['build_pdf_when_published'] = True
