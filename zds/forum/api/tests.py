# coding: utf-8

from django.conf import settings
from django.core.cache import caches
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.db import transaction
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from oauth2_provider.models import Application, AccessToken
from rest_framework_extensions.settings import extensions_api_settings
from zds.api.pagination import REST_PAGE_SIZE, REST_MAX_PAGE_SIZE, REST_PAGE_SIZE_QUERY_PARAM
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.forum.models import Forum, Topic, Post
from zds.forum.factories import PostFactory, TagFactory
from zds.forum.tests.tests_views import create_category, add_topic_in_a_forum
from zds.utils.models import CommentVote, Alert

# We remove spam limit so that we dont get 403 during testing
# Note : Spam limit is reactivated for the following test : test_create_post_spamming
overrided_zds_app = settings.ZDS_APP
overrided_zds_app['forum']['spam_limit_seconds'] = 0


class ForumPostKarmaAPITest(APITestCase):
    def setUp(self):

        self.client = APIClient()
        self.profile = ProfileFactory()

        client_oauth2 = create_oauth2_client(self.profile.user)
        self.client_authenticated = APIClient()
        authenticate_client(self.client_authenticated, client_oauth2, self.profile.user.username, 'hostel77')

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_failure_post_karma_with_client_unauthenticated(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=2)

        response = self.client.put(reverse('api:forum:post-karma', args=(post.pk,)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_failure_post_karma_with_sanctioned_user(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:post-karma', args=(post.pk,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_post_karma_with_a_message_not_found(self):
        response = self.client.get(reverse('api:forum:post-karma', args=(99999,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_failure_post_karma_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:post-karma', args=(topic.last_message.pk,)), {'vote': 'like'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success_post_karma_like(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:post-karma', args=(post.pk,)), {'vote': 'like'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=post, positive=True).exists())

    def test_success_post_karma_dislike(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:post-karma', args=(post.pk,)), {'vote': 'dislike'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentVote.objects.filter(user=profile.user, comment=post, positive=False).exists())

    def test_success_post_karma_neutral(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        vote = CommentVote(user=profile.user, comment=post, positive=True)
        vote.save()

        self.assertTrue(CommentVote.objects.filter(pk=vote.pk).exists())
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:post-karma', args=(post.pk,)), {'vote': 'neutral'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk).exists())

    def test_success_post_karma_like_already_disliked(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=2)

        vote = CommentVote(user=profile.user, comment=post, positive=False)
        vote.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:post-karma', args=(post.pk,)), {'vote': 'like'})
        vote.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(vote.positive)

    def test_get_post_voters(self):
        profile = ProfileFactory()
        profile2 = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
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

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))

        # on first message we should see 2 likes and 0 anonymous
        response = self.client.get(reverse('api:forum:post-karma', args=[upvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data['like']['users']))
        self.assertEqual(0, len(response.data['dislike']['users']))
        self.assertEqual(2, response.data['like']['count'])
        self.assertEqual(0, response.data['dislike']['count'])

        # on second message we should see 2 dislikes and 0 anonymous
        response = self.client.get(reverse('api:forum:post-karma', args=[downvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data['like']['users']))
        self.assertEqual(2, len(response.data['dislike']['users']))
        self.assertEqual(0, response.data['like']['count'])
        self.assertEqual(2, response.data['dislike']['count'])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse('api:forum:post-karma', args=[equal_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['like']['users']))
        self.assertEqual(1, len(response.data['dislike']['users']))
        self.assertEqual(1, response.data['like']['count'])
        self.assertEqual(1, response.data['dislike']['count'])

        # Now we change the settings to keep anonymous the first [dis]like
        settings.VOTES_ID_LIMIT = anon_limit.pk
        # and we run the same tests
        # on first message we should see 1 like and 1 anonymous
        response = self.client.get(reverse('api:forum:post-karma', args=[upvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['like']['users']))
        self.assertEqual(0, len(response.data['dislike']['users']))
        self.assertEqual(2, response.data['like']['count'])
        self.assertEqual(0, response.data['dislike']['count'])

        # on second message we should see 1 dislikes and 1 anonymous
        response = self.client.get(reverse('api:forum:post-karma', args=[downvoted_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data['like']['users']))
        self.assertEqual(1, len(response.data['dislike']['users']))
        self.assertEqual(0, response.data['like']['count'])
        self.assertEqual(2, response.data['dislike']['count'])

        # on third message we should see 1 like and 1 dislike and 0 anonymous
        response = self.client.get(reverse('api:forum:post-karma', args=[equal_answer.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['like']['users']))
        self.assertEqual(1, len(response.data['dislike']['users']))
        self.assertEqual(1, response.data['like']['count'])
        self.assertEqual(1, response.data['dislike']['count'])


# TODO a reactiver @override_settings(ZDS_APP=overrided_zds_app)
class ForumAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.profile = ProfileFactory()
        client_oauth2 = create_oauth2_client(self.profile.user)
        self.client_authenticated = APIClient()
        authenticate_client(self.client_authenticated, client_oauth2, self.profile.user.username, 'hostel77')

        self.staff = StaffProfileFactory()
        client_oauth2 = create_oauth2_client(self.staff.user)
        self.client_authenticated_staff = APIClient()
        authenticate_client(self.client_authenticated_staff, client_oauth2, self.staff.user.username, 'hostel77')

        self.group_staff = Group.objects.filter(name="staff").first()

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def create_multiple_forums(self, number_of_forum=REST_PAGE_SIZE):
        for forum in xrange(0, number_of_forum):
            category, forum = create_category()

    def create_multiple_forums_with_topics(self, number_of_forum=REST_PAGE_SIZE, number_of_topic=REST_PAGE_SIZE, profile=None):
        if profile is None:
            profile = ProfileFactory()
        for forum in xrange(0, number_of_forum):
            category, forum = create_category()
            for topic in xrange(0, number_of_topic):
                new_topic = add_topic_in_a_forum(forum, profile)
        if number_of_forum == 1 and number_of_topic == 1:
            return new_topic

    def create_topic_with_post(self, number_of_post=REST_PAGE_SIZE, profile=None):
        if profile is None:
            profile = ProfileFactory()

        category, forum = create_category()
        new_topic = add_topic_in_a_forum(forum, profile)
        posts = []

        for post in xrange(0, number_of_post):
            posts.append(PostFactory(topic=new_topic, author=profile.user, position=2))

        return new_topic, posts

    def test_list_of_forums_empty(self):
        """
        Gets empty list of forums in the database.
        """
        response = self.client.get(reverse('api:forum:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_forums(self):
        """
        Gets list of forums not empty in the database.
        """
        self.create_multiple_forums()

        response = self.client.get(reverse('api:forum:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_forums_private(self):
        """
        Gets list of private forums not empty in the database (only for staff).
        """
        category, forum = create_category(self.group_staff)

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client_authenticated.get(reverse('api:forum:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client_authenticated_staff.get(reverse('api:forum:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1) # TODO nombre a affiner en fonction de la realite

    def test_list_of_forums_with_several_pages(self):
        """
        Gets list of forums with several pages in the database.
        """
        self.create_multiple_forums(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse('api:forum:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

        response = self.client.get(reverse('api:forum:list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), 1)

    def test_list_of_forums_for_a_page_given(self):
        """
        Gets list of forums with several pages and gets a page different that the first one.
        """
        self.create_multiple_forums(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse('api:forum:list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_forums_for_a_wrong_page_given(self):
        """
        Gets an error when the forums asks a wrong page.
        """
        response = self.client.get(reverse('api:forum:list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_forums_with_a_custom_page_size(self):
        """
        Gets list of forums with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_forums(REST_PAGE_SIZE * 2)

        page_size = 'page_size'
        response = self.client.get(reverse('api:forum:list') + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_forums_with_a_wrong_custom_page_size(self):
        """
        Gets list of forums with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_forums(page_size_value)

        response = self.client.get(reverse('api:forum:list') + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_details_forum(self):
        """
        Tries to get the details of a forum.
        """

        category, forum = create_category()
        response = self.client.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('id'), forum.id)
        self.assertEqual(response.data.get('title'), forum.title)
        self.assertEqual(response.data.get('subtitle'), forum.subtitle)
        self.assertEqual(response.data.get('slug'), forum.slug)
        self.assertEqual(response.data.get('category'), forum.category.id)
        self.assertEqual(response.data.get('position_in_category'), forum.position_in_category)
        self.assertEqual(response.data.get('group'), list(forum.group.all()))

    def test_details_forum_private(self):
        """
        Tries to get the details of a private forum with different users.
        """
        category, forum = create_category(self.group_staff)

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_details_unknown_forum(self):
        """
        Tries to get the details of a forum that does not exists.
        """

        self.create_multiple_forums(1)
        response = self.client.get(reverse('api:forum:detail', args=[3]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_details_private_forum_user(self):
        """
        Tries to get the details of a private forum with a normal user, staff user and anonymous one.
        """
        category, forum = create_category(self.group_staff)

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# TODO
# Récupérer la liste des sujets en filtrant tag, forum, auteur (resulat non vide)

    def test_list_of_topics_empty(self):
        """
        Gets empty list of topics in the database.
        """
        response = self.client.get(reverse('api:forum:list-topic'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_topics(self):
        """
        Gets list of topics not empty in the database.
        """
        self.create_multiple_forums_with_topics(1)
        response = self.client.get(reverse('api:forum:list-topic'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_topics_with_several_pages(self):
        """
        Gets list of topics with several pages in the database.
        """
        self.create_multiple_forums_with_topics(1, REST_PAGE_SIZE + 1)

        response = self.client.get(reverse('api:forum:list-topic'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

        response = self.client.get(reverse('api:forum:list-topic') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), 1)

    def test_list_of_topics_for_a_page_given(self):
        """
        Gets list of topics with several pages and gets a page different that the first one.
        """
        self.create_multiple_forums_with_topics(1, REST_PAGE_SIZE + 1)

        response = self.client.get(reverse('api:forum:list-topic') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_topics_for_a_wrong_page_given(self):
        """
        Gets an error when the topics asks a wrong page.
        """
        response = self.client.get(reverse('api:forum:list-topic') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_topics_with_a_custom_page_size(self):
        """
        Gets list of topics with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_forums_with_topics(1, REST_PAGE_SIZE * 2)

        page_size = 'page_size'
        response = self.client.get(reverse('api:forum:list-topic') + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_topics_with_a_wrong_custom_page_size(self):
        """
        Gets list of topics with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_forums_with_topics(1, page_size_value)

        response = self.client.get(reverse('api:forum:list-topic') + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_list_of_topics_with_forum_filter_empty(self):
        """
        Gets an empty list of topics in a forum.
        """
        self.create_multiple_forums_with_topics(1)
        response = self.client.get(reverse('api:forum:list-topic') + '?forum=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_topics_with_forum_filter(self):
        """
        Gets a list of topics in a forum.
        """
        self.create_multiple_forums_with_topics(1)
        forum = Forum.objects.all().first()
        response = self.client.get(reverse('api:forum:list-topic') + '?forum=' + str(forum.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

    def test_list_of_topics_with_author_filter_empty(self):
        """
        Gets an empty list of topics created by an user.
        """
        self.create_multiple_forums_with_topics(1)
        response = self.client.get(reverse('api:forum:list-topic') + '?author=6')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_topics_with_author_filter(self):
        """
        Gets a list of topics created by an user.
        """
        self.create_multiple_forums_with_topics(1, REST_PAGE_SIZE, self.profile)
        response = self.client.get(reverse('api:forum:list-topic') + '?author=' + str(self.profile.user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

    def test_list_of_topics_with_tag_filter_empty(self):
        """
        Gets an empty list of topics with a specific tag.
        """
        self.create_multiple_forums_with_topics(1)
        response = self.client.get(reverse('api:forum:list-topic') + '?tags__title=ilovezozor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_topics_with_tag_filter(self):
        """
        Gets a list of topics with a specific tag.
        """
        self.create_multiple_forums_with_topics(1, REST_PAGE_SIZE)
        topic = Topic.objects.first()
        tag = TagFactory()
        topic.add_tags([tag.title])

        response = self.client.get(reverse('api:forum:list-topic') + '?tags=' + str(tag.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_new_topic_with_user(self):
        """
        Post a new topic in a forum with an user.
        """
        self.create_multiple_forums()
        tag = TagFactory()

        data = {
            'title': 'Flask 4 Ever !',
            'subtitle': 'Is it the best framework ?',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 1,
            'tags': [tag]
        }

        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        topic = Topic.objects.filter(author=self.profile.user.id).first()
        self.assertEqual(response.data.get('title'), topic.title)
        self.assertEqual(response.data.get('subtitle'), topic.subtitle)
        self.assertEqual(data.get('text'), topic.last_message.text)
        self.assertEqual(response.data.get('author'), self.profile.user.id)
        self.assertIsNotNone(response.data.get('last_message'))
        self.assertIsNotNone(response.data.get('pubdate'))

    def test_new_topic_with_anonymous(self):
        """
        Post a new topic in a forum with an anonymous user.
        """
        self.create_multiple_forums()
        data = {
            'title': 'Flask 4 Ever !',
            'subtitle': 'Is it the best framework ?',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 1
        }
        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_topic_private_forum(self):
        """
        Post a new topic in a private forum (staff only) with an anonymous user, normal user and staff user.
        """
        profile = ProfileFactory()
        self.group_staff.user_set.add(profile.user)
        category, forum = create_category(self.group_staff)
        data = {
            'title': 'Have you seen the guy flooding ?',
            'subtitle': 'He is asking to many question about flask.',
            'text': 'Should we ban him ? I think we should.',
            'forum': forum.id
        }

        # Anonymous
        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User
        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        response = self.client_authenticated_staff.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_new_topic_with_banned_user(self):

        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        self.create_multiple_forums()
        data = {
            'title': 'Flask 4 Ever !',
            'subtitle': 'Is it the best framework ?',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 1
        }

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_new_topic_without_title(self):
        """
        Try to post a new topic in a forum without the title
        """
        self.create_multiple_forums()
        data = {
            'subtitle': 'Is it the best framework ?',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 1
        }

        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_topic_without_subtitle(self):
        """
        Try to post a new topic in a forum without the title
        """
        self.create_multiple_forums()
        data = {
            'title': 'Flask 4 Ever !',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 1
        }

        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_new_topic_without_text(self):
        """
        Try to post a new topic in a forum without the text.
        """
        self.create_multiple_forums()
        data = {
            'title': 'Flask 4 Ever !',
            'subtitle': 'Is it the best framework ?',
            'forum': 1
        }

        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_topic_in_unknow_forum(self):
        """
        Try to post a new topic in a forum that does not exists.
        """
        self.create_multiple_forums()
        data = {
            'title': 'Flask 4 Ever !',
            'subtitle': 'Is it the best framework ?',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 666
        }

        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_details_topic(self):
        """
        Get details of a topic.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        tag = TagFactory()
        tag2 = TagFactory()
        topic.add_tags([tag.title, tag2.title])

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=(topic.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), topic.title)
        self.assertEqual(response.data.get('subtitle'), topic.subtitle)
        self.assertEqual(response.data.get('forum'), topic.forum.id)
        self.assertEqual(response.data.get('tags'), [tag.id, tag2.id])
        self.assertIsNotNone(response.data.get('title'))
        self.assertIsNotNone(response.data.get('forum'))
        self.assertIsNone(response.data.get('ip_address'))

    def test_details_unknown_topic(self):
        """
        Get details of a topic that doesw not exist.
        """

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=[666]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_details_topic_private(self):
        """
        Tries to get details of a topic that is in a private forum.
        """
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, self.staff)

        # Anonymous
        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User
        response = self.client_authenticated.get(reverse('api:forum:detail-topic', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        response = self.client_authenticated_staff.get(reverse('api:forum:detail-topic', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_details_topic_with_post_hidden(self):
        """
        Get details of a topic where the first post is hidden.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        tag = TagFactory()
        tag2 = TagFactory()
        topic.add_tags([tag.title, tag2.title])
        topic.is_visible = False

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=(topic.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), topic.title)
        self.assertEqual(response.data.get('subtitle'), topic.subtitle)
        self.assertEqual(response.data.get('forum'), topic.forum.id)
        self.assertEqual(response.data.get('tags'), [tag.id, tag2.id])
        self.assertIsNotNone(response.data.get('title'))
        self.assertIsNotNone(response.data.get('forum'))
        self.assertIsNone(response.data.get('ip_address'))
        self.assertIsNone(response.data.get('text'))
        self.assertIsNone(response.data.get('text_html'))
        self.assertFalse(response.data.get('is_visible'))

    def test_update_topic_details_title(self):
        """
        Updates title of a topic.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), data.get('title'))

    def test_update_topic_details_title_empty(self):
        """
        Updates title of a topic, tries to put an empty sting
        """
        data = {
            'title': ''
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_topic_details_subtitle(self):
        """
        Updates subtitle of a topic.
        """
        data = {
            'subtitle': 'Mon nouveau sous-titre'
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('subtitle'), data.get('subtitle'))

    def test_update_topic_anonymous(self):
        """
        Tries to update a Topic with an anonymous user.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        topic = self.create_multiple_forums_with_topics(1, 1)
        self.client = APIClient()
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_topic_banned_user(self):
        """
        Tries to update a Topic with a banned user.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        topic = self.create_multiple_forums_with_topics(1, 1)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_topic_staff(self):
        """
        Updates title of a topic with a staff member.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), data.get('title'))

    def test_update_topic_other_user(self):
        """
        Tries to update title of a topic posted by another user.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        profile = ProfileFactory()
        topic = self.create_multiple_forums_with_topics(1, 1, profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_unknown_topic(self):
        """
        Tries to update title of a non existing topic.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[666]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_topic_forum(self):
        """
        Tries to move (change forum in which the topic is) with different users.
        """
        data = {
            'forum': 5
        }
        profile = ProfileFactory()
        self.create_multiple_forums_with_topics(5, 1, profile)
        topic = Topic.objects.filter(forum=1).first()

        # Anonymous
        self.client = APIClient()
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('forum'), data.get('forum'))

    def test_update_topic_lock(self):
        """
        Tries to lock a Topic with different users.
        """
        data = {
            'is_locked': True
        }
        topic = self.create_multiple_forums_with_topics(1, 1)

        self.client = APIClient()
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('is_locked'))

    def test_update_topic_private_forum(self):
        """
        Tries to update a Topic in a private forum with different users.
        """
        data = {
            'title': 'Mon nouveau titre'
        }

        profile = StaffProfileFactory()
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, profile)

        self.client = APIClient()
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get('title'), response.data.get('title'))
        topic = Topic.objects.get(pk=topic.id)
        self.assertEqual(data.get('title'), topic.title)

    def test_update_topic_solve(self):
        """
        Tries to solve a Topic with different users.
        """
        data = {
            'is_solved': True
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)

        self.client = APIClient()
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Author
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('is_solved'))

        # Other user
        other_profile = ProfileFactory()
        client_oauth2 = create_oauth2_client(other_profile.user)
        client_other_user = APIClient()
        authenticate_client(client_other_user, client_oauth2, other_profile.user.username, 'hostel77')

        response = client_other_user.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('is_solved'))

    def test_list_of_posts_unknown(self):
        """
        Tries to get a list of posts in an unknown topic
        """
        response = self.client.get(reverse('api:forum:list-post', args=[666]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_posts(self):
        """
        Gets list of posts in a topic.
        """
        # A post is already included with the topic
        topic, posts = self.create_topic_with_post(REST_PAGE_SIZE - 1)

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_posts_private_forum(self):
        """
        Get a list of posts in a topic of a private forum.
        """
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        group.user_set.add(profile.user)
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)
        # TODO c'est quoi ce test ???
        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_posts_private_forum_user(self):
        """
        Tries to get a list of posts in a topic of a private forum with a normal user.
        """
        profile = ProfileFactory()
        self.group_staff.user_set.add(profile.user)
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client_authenticated.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_of_posts_with_several_pages(self):
        """
        Gets list of posts with several pages in the database.
        """
        topic, posts = self.create_topic_with_post(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 2) # Note : when creating a Topic a first post is created, explaining the +1
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 2)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), 2)

    def test_list_of_posts_for_a_page_given(self):
        """
        Gets list of posts with several pages and gets a page different that the first one.
        """
        topic, posts = self.create_topic_with_post(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 12)
        self.assertEqual(len(response.data.get('results')), 2)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_posts_for_a_wrong_page_given(self):
        """
        Gets an error when the posts asks a wrong page.
        """
        topic, posts = self.create_topic_with_post(1)
        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_posts_with_a_custom_page_size(self):
        """
        Gets list of forums with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        topic, posts = self.create_topic_with_post((REST_PAGE_SIZE * 2) - 1)

        page_size = 'page_size'
        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]) + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_posts_in_topic_with_a_wrong_custom_page_size(self):
        """
        Gets list of posts with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        topic, posts = self.create_topic_with_post(page_size_value)

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]) + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # We will have page_size_value + 1 because a post is added at topic creation.
        self.assertEqual(response.data.get('count'), page_size_value + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_list_of_posts_in_unknown_topic(self):
        """
        Tries to list the posts of an non existing Topic.
        """

        response = self.client.get(reverse('api:forum:list-post', args=[666]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_posts_with_hidden_post(self):
        """
        Gets list of posts in a topic with two that are hidden.
        """
        # A post is already included with the topic
        topic, posts = self.create_topic_with_post(20)

        # Post hidden by user
        post = posts[4]
        post.is_visible = False
        post.save()

        # Post hidden by staff member
        another_post = posts[5]
        another_post.is_visible = False
        another_post.text_hidden = 'Flood'
        another_post.save()

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.data.get('results')[4].text)
        self.assertIsNone(response.data.get('results')[4].text_html)
        self.assertIsFalse(response.data.get('results')[4].is_visible)

        self.assertIsNone(response.data.get('results')[5].text)
        self.assertIsNone(response.data.get('results')[5].text_html)
        self.assertIsFalse(response.data.get('results')[5].is_visible)
        self.assertIsEqual(response.data.get('results')[5].text_hidden, 'Flood')

    def test_list_of_user_topics_empty(self):
        """
        Gets empty list of topic that the user created.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-usertopic'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_user_topics(self):
        """
        Gets list of user's topics not empty in the database.
        """
        self.create_multiple_forums_with_topics(10, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-usertopic'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 10)
        self.assertEqual(len(response.data.get('results')), 10)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_user_topics_with_several_pages(self):
        """
        Gets list of user's topics with several pages in the database.
        """
        self.create_multiple_forums_with_topics(REST_PAGE_SIZE + 1, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-usertopic'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

        response = self.client_authenticated.get(reverse('api:forum:list-usertopic') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), 1)

    def test_list_of_user_topics_for_a_page_given(self):
        """
        Gets list of user's topics with several pages and gets a page different that the first one.
        """
        self.create_multiple_forums_with_topics(REST_PAGE_SIZE + 1, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-usertopic') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_users_topics_for_a_wrong_page_given(self):
        """
        Gets an error when the user's topics asks a wrong page.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-usertopic') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_user_topics_with_a_custom_page_size(self):
        """
        Gets list of user's topics with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_forums_with_topics(REST_PAGE_SIZE * 2, 1, self.profile)

        page_size = 'page_size'
        response = self.client_authenticated.get(reverse('api:forum:list-usertopic') + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_user_topics_with_a_wrong_custom_page_size(self):
        """
        Gets list of user's topic with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_forums_with_topics(page_size_value, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-usertopic') + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_list_of_user_topics_anonymous(self):
        """
        Tries to get a list of users topic with an anonymous user.
        """
        self.client = APIClient()
        response = self.client.get(reverse('api:forum:list-usertopic'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_with_no_field(self):
        """
        Creates a post in a topic but not with according field.
        """
        topic = self.create_multiple_forums_with_topics(1, 1, self.staff)
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_with_empty_field(self):
        """
        Creates a post in a topic but with no text.
        """
        data = {
            'text': ''
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.staff)
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_unauthenticated(self):
        """
        Creates a post in a topic with unauthenticated client.
        """
        data = {
            'text': 'Welcome to this post!'
        }

        topic = self.create_multiple_forums_with_topics(1, 1)
        self.client = APIClient()
        with transaction.atomic():
            response = self.client.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_locked_topic(self):
        """
        Tries to create a post in a locked topic.
        """
        data = {
            'text': 'Welcome to this post!'
        }
        profile = ProfileFactory()
        category, forum = create_category()
        # Create a locked topic
        topic = add_topic_in_a_forum(forum, profile, False, False, True)

        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post = Post.objects.filter(topic=topic.id).last()
        self.assertEqual(response.data.get('text'), data.get('text'))
        self.assertEqual(post.text, data.get('text'))

    def test_create_post_with_bad_topic_id(self):
        """
        Creates a post in a topic with a bad topic id.
        """
        data = {
            'text': 'Welcome to this post!'
        }
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[666]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_post(self):
        """
        Creates a post in a topic.
        """
        data = {
            'text': 'Welcome to this post!'
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.staff)
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.filter(topic=topic.id).last()

        self.assertEqual(response.data.get('text'), data.get('text'))
        self.assertEqual(response.data.get('text'), post.text)
        self.assertEqual(response.data.get('is_useful'), post.is_useful)
        self.assertEqual(response.data.get('author'), post.author.id)
        self.assertEqual(response.data.get('position'), post.position)

    # TODO reactiver le setting pour le spam
    def test_create_post_spamming(self):
        """
        Tries to create differents posts in the same Topic without waiting 15 minutes.
        """

        data = {
            'text': 'Welcome to this post!'
        }

        # First post, should work alright
        topic = self.create_multiple_forums_with_topics(1, 1, self.staff)
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # But this is spam
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_post_in_a_forum_we_cannot_read(self):
        """
        Tries to create a post in a private topic with a normal user.
        """
        profile = StaffProfileFactory()
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, profile)
        data = {
            'text': 'Welcome to this post!'
        }
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.pk]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_in_a_private_forum(self):
        """
        Post in a private topic with a user that has access right.
        """

        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, self.staff)
        data = {
            'text': 'Welcome to this post!'
        }
        response = self.client_authenticated_staff.post(reverse('api:forum:list-post', args=[topic.pk]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.filter(topic=topic.id).last()
        self.assertEqual(response.data.get('text'), data.get('text'))
        self.assertEqual(response.data.get('text'), post.text)
        self.assertEqual(response.data.get('is_useful'), post.is_useful)
        self.assertEqual(response.data.get('author'), post.author.id)
        self.assertEqual(response.data.get('position'), post.position)

    def test_new_post_user_with_restrictions(self):
        """
        Try to post a new post with an user that has some restrictions .
        """

        # Banned
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        topic = self.create_multiple_forums_with_topics(1, 1)
        data = {
            'text': 'I head that Flask is the best framework ever, is that true ?'
        }

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Read only
        profile = ProfileFactory()
        profile.can_write = False
        profile.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_post(self):
        """
        Gets all information about a post.
        """

        topic, posts = self.create_topic_with_post()
        post = posts[0]
        response = self.client.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(post.id, response.data.get('id'))
        self.assertIsNotNone(response.data.get('text'))
        self.assertIsNotNone(response.data.get('text_html'))
        self.assertIsNotNone(response.data.get('pubdate'))
        self.assertIsNone(response.data.get('update'))
        self.assertEqual(post.position, response.data.get('position'))
        self.assertEqual(topic.author.id, response.data.get('author'))
        self.assertIsNone(response.data.get('ip_address'))

    def test_detail_of_a_private_post_not_present(self):
        """
        Gets an error 404 when the post isn't present in the database.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        response = self.client.get(reverse('api:forum:detail-post', args=[topic.id, 666]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_of_private_post(self):
        """
        Tries to get all the data about a post in a private topic (and forum) with different users.
        """
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, self.profile)
        post = Post.objects.filter(topic=topic.id).first()

        # Anonymous
        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User
        response = self.client_authenticated.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        response = self.client_authenticated_staff.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_of_member_posts_empty(self):
        """
        Gets empty list of posts that that a specified member created.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_member_posts(self):
        """
        Gets list of a member posts not empty in the database.
        """
        self.create_multiple_forums_with_topics(10, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 10)
        self.assertEqual(len(response.data.get('results')), 10)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_staff_posts(self):
        """
        Gets list of a staff posts.
        """

        profile = StaffProfileFactory()
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, profile)

        # Anonymous user cannot see staff private post.
        self.client = APIClient()
        response = self.client.get(reverse('api:forum:list-memberpost', args=[profile.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        # Same for normal user
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[profile.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client_authenticated_staff.get(reverse('api:forum:list-memberpost', args=[profile.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_list_of_member_posts_with_several_pages(self):
        """
        Gets list of a member topics with several pages in the database.
        """
        self.create_multiple_forums_with_topics(REST_PAGE_SIZE + 1, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), 1)

    def test_list_of_member_posts_for_a_page_given(self):
        """
        Gets list of a member topics with several pages and gets a page different that the first one.
        """

        self.create_multiple_forums_with_topics(REST_PAGE_SIZE + 1, 1, self.profile)
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id])+ '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_member_post_for_a_wrong_page_given(self):
        """
        Gets an error when the member posts asks a wrong page.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_member_posts_with_a_custom_page_size(self):
        """
        Gets list of user's posts with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        # When a topic is created, a post is also created.
        self.create_topic_with_post((REST_PAGE_SIZE * 2) - 1, self.profile)

        page_size = 'page_size'
        response = self.client.get(reverse('api:forum:list-memberpost', args=[self.profile.id]) + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_member_posts_with_a_wrong_custom_page_size(self):
        """
        Gets list of member posts with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_forums_with_topics(page_size_value, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[self.profile.id]) + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_list_of_unknow_member_posts(self):
        """
        Gets empty list of posts for a member that does not exists.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost', args=[666]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_alert_post(self):
        """
        Tries to alert a post in a public forum with different type of users
        """
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_profile = ProfileFactory()
        post = PostFactory(topic=topic, author=another_profile.user, position=1)
        data = {
            'text': 'There is a guy flooding about Flask, can you do something about it ?'
        }

        self.client = APIClient()
        response = self.client.post(reverse('api:forum:alert-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.post(reverse('api:forum:alert-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        alerte = Alert.objects.latest('pubdate')
        self.assertEqual(alerte.text, data.get('text'))
        self.assertEqual(alerte.author, self.profile.user)
        self.assertEqual(alerte.comment.id, post.id)


    def test_alert_post_in_private_forum(self):
        """
        Tries to alert a post in a public forum with different type of users
        """
        profile = StaffProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=1)
        data = {
            'text': 'There is a guy flooding about Flask, con you do something about it ?'
        }

        self.client = APIClient()
        response = self.client.post(reverse('api:forum:alert-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.post(reverse('api:forum:alert-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.post(reverse('api:forum:alert-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        alerte = Alert.objects.latest('pubdate')
        self.assertEqual(alerte.text, data.get('text'))
        self.assertEqual(alerte.author, self.client_authenticated_staff)
        self.assertEqual(alerte.comment, post.id)

    def test_alert_post_not_found(self):
        """
        Tries to alert a post in a public forum with different type of users
        """
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=1)
        data = {
            'text': 'There is a guy flooding about Flask, con you do something about it ?'
        }

        response = self.client_authenticated.post(reverse('api:forum:alert-post', args=[topic.id, 666]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_alert_with_banned_user(self):

        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=1)
        data = {
            'text': 'I am the one that flood, this is why I am banned. Please, I have changed !'
        }

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('api:forum:alert-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_post_anonymous(self):
        """
        Tries to update a post with anonymous user.
        """
        data = {
            'text': 'I made an error I want to edit.'
        }
        self.client = APIClient()
        topic, posts = self.create_topic_with_post()
        response = self.client.put(reverse('api:forum:detail-post', args=[topic.id, posts[0].id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_post_other_user(self):
        """
        Tries to update a post with another user that the one who posted on the first time.
        """
        data = {
            'text': 'I made an error I want to edit.'
        }
        another_profile = ProfileFactory()
        topic, posts = self.create_topic_with_post(REST_PAGE_SIZE, another_profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[topic.id, posts[0].id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_post(self):
        """
        Updates a post with user.
        """
        data = {
            'text': 'I made an error I want to edit.'
        }
        topic, posts = self.create_topic_with_post(1, self.profile)

        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[topic.id, posts[0].id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), data.get('text'))
        self.assertEqual(response.data.get('editor'), self.profile.user.id)
        self.assertIsNotNone(response.data.get('update'))

    def test_update_post_text_empty(self):
        """
        Tries to empty the text of a post.
        """
        data = {
            'text': ''
        }
        topic, posts = self.create_topic_with_post(1, self.profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[topic.id, posts[0].id]), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_post_staff(self):
        """
        Update a post with a staff user.
        """
        data = {
            'text': 'I am Vladimir Lupin, I do want I want.'
        }
        topic, posts = self.create_topic_with_post()
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-post', args=[topic.id, posts[0].id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), data.get('text'))

    def test_update_unknow_post(self):
        """
        Tries to update post that does not exist.
        """
        data = {
            'text': 'I made an error I want to edit.'
        }
        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[666, 42]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post_in_private_topic(self):
        """
        Tries to update a post in a private forum (and topic) with different users.
        """
        data = {
            'text': 'I made an error I want to edit.'
        }
        self.client = APIClient()
        category, forum = create_category(self.group_staff)
        topic = add_topic_in_a_forum(forum, self.staff)
        post = PostFactory(topic=topic, author=self.staff.user, position=1)

        # With anonymous
        response = self.client.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # With user
        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # With staff (member of private forum)
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get('text'), response.data.get('text'))

    def test_update_post_in_locked_topic(self):
        """
        Tries to update a post in a locked topic with different users.
        """
        data = {
            'text': 'I made an error I want to edit.'
        }
        self.client = APIClient()
        category, forum = create_category()
        # Create locked topic
        topic = add_topic_in_a_forum(forum, self.profile, False, False, True)
        post = PostFactory(topic=topic, author=self.profile.user, position=1)

        # With anonymous
        response = self.client.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # With user
        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # With staff
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get('text'), response.data.get('text'))

    def test_update_post_hide_post(self):
        """
        Tries to update a post in a forum to hide the content of the post (different users).
        """
        data = {
            'is_visible': False,
            'text_hidden': 'Flood'
        }

        data_user = {
            'is_visible': False,
        }

        self.client = APIClient()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, self.staff)
        post = PostFactory(topic=topic, author=self.profile.user, position=1)

        # With anonymous
        response = self.client.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # With user
        response = self.client_authenticated.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertIsNone(response.data.get('text_html'))
        self.assertIsNone(response.data.get('text'))
        self.assertFalse(response.data.get('is_visible'))

        # With staff
        response = self.client_authenticated_staff.put(reverse('api:forum:detail-post', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text_hidden'), data.get('text_hidden'))
        self.assertIsNone(response.data.get('text_html'))
        self.assertIsNone(response.data.get('text'))
        self.assertFalse(response.data.get('is_visible'))

def create_oauth2_client(user):
    client = Application.objects.create(user=user,
                                        client_type=Application.CLIENT_CONFIDENTIAL,
                                        authorization_grant_type=Application.GRANT_PASSWORD)
    client.save()
    return client


def authenticate_client(client, client_auth, username, password):
    client.post('/oauth2/token/', {
        'client_id': client_auth.client_id,
        'client_secret': client_auth.client_secret,
        'username': username,
        'password': password,
        'grant_type': 'password'
    })
    access_token = AccessToken.objects.get(user__username=username)
    client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

# TODO
# Reorganiser le code de test en differentes classes, reordonner les tests

# A la création de topic pouvoir mettre des tags
# A l'édit de topic pouvoir changer des tags
# Tests qui ne passent pas
# Style / PEP8
# Route listant les Tags ?
# quand on poste un message dans un topic depuis l'API il semblerait que la position dans le topic ne soit pas bonne

# TESTS MANQUANTS
# ALLOWED_HOSTS=['zds-anto59290.c9users.io']
