# coding: utf-8

from django.conf import settings
from django.core.cache import caches
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from oauth2_provider.models import Application, AccessToken
from rest_framework_extensions.settings import extensions_api_settings
from zds.api.pagination import REST_PAGE_SIZE, REST_MAX_PAGE_SIZE, REST_PAGE_SIZE_QUERY_PARAM
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.forum.models import Forum, Topic, Post
from zds.forum.factories import PostFactory
from zds.forum.tests.tests_views import create_category, add_topic_in_a_forum
from zds.utils.models import CommentVote


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

# Liste les forums avec un staff (on boit les forums privé)


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

        for post in xrange(0, number_of_post):
            PostFactory(topic=new_topic.id, author=profile.user, position=2)

        return new_topic

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
        self.assertEqual(response.data.get('category'), forum.category)
        self.assertEqual(response.data.get('position_in_category'), forum.position_in_category)
        self.assertEqual(response.data.get('group'), forum.group)

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
        group = Group.objects.create(name="staff")
        category, forum = create_category(group)

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authentificated.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authentificated_staff.get(reverse('api:forum:detail', args=[forum.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# TODO
# Récupérer la liste des sujets en filtrant sur l'auteur (resulat non vide)
# Récupérer la liste des sujets en filtrant sur le tag (resulat non vide)
# Récupérer la liste des sujets en filtrant sur le forum (resulat non vide)
# Récupérer la liste des sujets en filtrant tag, forum, auteur (resulat non vide)
# Idem avec un tag inexistant NE MARCHE PAS

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

    def test_list_of_topics_with_tag_filter_empty(self):
        """
        Gets an empty list of topics with a specific tag.
        """
        self.create_multiple_forums_with_topics(1)
        response = self.client.get(reverse('api:forum:list-topic') + '?tag=ilovezozor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_new_topic_with_user(self):
        """
        Post a new topic in a forum with an user.
        """
        self.create_multiple_forums()
        data = {
            'title': 'Flask 4 Ever !',
            'subtitle': 'Is it the best framework ?',
            'text': 'I head that Flask is the best framework ever, is that true ?',
            'forum': 1
        }

        response = self.client_authenticated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        topics = Topic.objects.filter(author=self.profile.user.id)
        print(topics[0])
        self.assertEqual(1, len(topics))
        self.assertEqual(response.data.get('title'), topics[0].title)
        self.assertEqual(response.data.get('subtitle'), topics[0].subtitle)
        # Todo ne fonctionne pas self.assertEqual(data.get('text'), topics[0].last_message.text)
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

        group = Group.objects.create(name="staff")

        profile = ProfileFactory()
        group.user_set.add(profile.user)
        category, forum = create_category(group)
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
        response = self.client_authentificated.post(reverse('api:forum:list-topic'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        response = self.client_authentificated_staff.post(reverse('api:forum:list-topic'), data)
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_details_topic(self):
        """
        Get details of a topic.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=(topic.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), topic.title)
        self.assertEqual(response.data.get('subtitle'), topic.subtitle)
        self.assertEqual(response.data.get('forum'), topic.forum.id)
        self.assertIsNotNone(response.data.get('title'))
        self.assertIsNotNone(response.data.get('forum'))

    def test_details_unknown_topic(self):
        """
        Get details of a topic that doesw not exist.
        """

        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=(666)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_details_topic_private(self):
        """
        Tries to get details of a topic that is in a private forum.
        """

        group = Group.objects.create(name="staff")
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, self.staff)

        # Anonymous
        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-topic', args=(topic.id)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User
        response = self.client_authenticated.get(reverse('api:forum:detail-topic', args=(topic.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        response = self.client_authenticated_staff.get(reverse('api:forum:detail-topic', args=(topic.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_new_post_anonymous(self):
        """
        Try to post a new post with anonymous user.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        data = {
            'text': 'I head that Flask is the best framework ever, is that true ?'
        }

        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-post', args=(topic.id)), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_post_user(self):
        """
        Try to post a new post with an user.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        data = {
            'text': 'I head that Flask is the best framework ever, is that true ?'
        }

        self.client = APIClient()
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=(topic.id)), data)
        topic = Topic.objects.filter(id=topic.id)
        print(topic)
        last_message = topic.get_last_post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('text'), last_message.text)

    def test_new_post_user_with_restrictions(self):
        """
        Try to post a new post with an user that has some restrictions .
        """
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        topic = self.create_multiple_forums_with_topics(1, 1)
        data = {
            'text': 'I head that Flask is the best framework ever, is that true ?'
        }

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('api:forum:list-post', args=(topic.id,)), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        profile = ProfileFactory()
        profile.can_write = False
        profile.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('api:forum:list-post', args=(topic.id,)), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_new_post_no_text(self):
        """
        Try to post a new post without a text.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        data = {}
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=(topic.id,)), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_post_empty_text(self):
        """
        Try to post a new post with an empty text.
        """
        topic = self.create_multiple_forums_with_topics(1, 1)
        data = {
            'text': ''
        }
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=(topic.id,)), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_post_unknown_topic(self):
        """
        Try to post a new post in a topic that does not exists.
        """
        data = {
            'text': 'Where should I go now ?'
        }
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=(666,)), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# Edite un sujet sans changement
# Édite un sujet qvec user en ls
# Édite un sujet avec user banni
# Édite un sujet en vidant le titre
# Édite un sujet en le passant en resolu
# Editer dans un forum privé ? Verifier les auths
# TODO

    def test_update_topic_details_title(self):
        """
        Updates title of a topic.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), data.get('title'))

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

    def test_update_topic_staff(self):
        """
        Updates title of a topic with a staff member.
        """
        data = {
            'title': 'Mon nouveau titre'
        }
        topic = self.create_multiple_forums_with_topics(1, 1, self.profile)
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
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
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
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

    def test_update_topic_forum_user(self):
        """
        Tries to move (change forum in which the topic is) with an user.
        """
        data = {
            'forum': 5
        }
        self.create_multiple_forums_with_topics(5, 1, self.profile)
        topic = Topic.objects.filter(forum=1).first()
        response = self.client.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_topic_forum_staff(self):
        """
        Tries to move (change forum in which the topic is) with a staff member.
        """
        data = {
            'forum': 5
        }
        self.create_multiple_forums_with_topics(5, 1, self.profile)
        topic = Topic.objects.filter(forum=1).first()
        response = self.client_authenticated.put(reverse('api:forum:detail-topic', args=[topic.id]), data)
        print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('forum'), data.get('forum'))

    def test_list_of_posts_unknown(self):
        """
        Tries to get a list of posts in an unknown topic
        """
        response = self.client.get(reverse('api:forum:list-post', args=[666]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_of_posts(self):
        """
        Gets list of posts in a topic.
        """
        topic = self.create_topic_with_post()

        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
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
        # def add_topic_in_a_forum(forum, profile, is_sticky=False, is_solved=False, is_locked=False):

        response = profile.client.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_posts_private_forum_user(self):
        """
        Tries to get a list of posts in a topic of a private forum with a normal user.
        """
        group = Group.objects.create(name="staff")

        profile = ProfileFactory()
        group.user_set.add(profile.user)
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client_authenticated.get(reverse('api:forum:list-post', args=[topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_posts_with_several_pages(self):
        """
        Gets list of posts with several pages in the database.
        """
        topic = self.create_topic_with_post(REST_PAGE_SIZE + 1)

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
        topic = self.create_topic_with_post(REST_PAGE_SIZE + 1)

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
        topic = self.create_topic_with_post(1)
        response = self.client.get(reverse('api:forum:list-post', args=[topic.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_posts_with_a_custom_page_size(self):
        """
        Gets list of forums with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        topic = self.create_topic_with_post(REST_PAGE_SIZE * 2)
        print (topic)

        page_size = 'page_size'
        response = self.client.get(reverse('api:forum:list-post') + '?{}=20'.format(page_size), args=[topic.id])
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
        topic = self.create_topic_with_post(page_size_value)

        response = self.client.get(reverse('api:forum:list-post') + '?page_size={}'.format(page_size_value), args=[topic.id])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_list_of_posts_in_unknown_topic(self):
        """
        Tries to list the posts of an non existing Topic.
        """
        topic = self.create_topic_with_post()

        response = self.client.get(reverse('api:forum:list-post'), args=[topic.id])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
        response = self.client.get(reverse('api:forum:list-usertopic') + '?{}=20'.format(page_size))
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

        response = self.client.get(reverse('api:forum:list-usertopic'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# DONE Créer un message 200
# DONE Créer un message avec un contenu vide
# DONECréer un message dans un sujet qui n'existe pas
# DONE Créer un message en anonymous
# Créer un message dans un sujet qui en contient deja
# DONE Créer un message dans un forum privé en user
# DONE Créer un message dans un forum privé en staff
# Créer un message dans un sujet fermé en user
# Créer un message dans un sujet fermé en staff
# Créer un message pour tester l'antiflood

    def test_create_post_with_no_field(self):
        """
        Creates a post in a topic but not with according field.
        """
        response = self.client.post(reverse('api:forum:list-post', args=[self.private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_with_empty_field(self):
        """
        Creates a post in a topic but with no text.
        """
        data = {
            'text': ''
        }
        response = self.client.post(reverse('api:forum:list-post', args=[self.private_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_unauthenticated(self):
        """
        Creates a post in a topic with unauthenticated client.
        """
        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-post', args=[0]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
        topic = create_multiple_forums_with_topics(1, 1)
        response = self.client_authenticated.post(reverse('api:forum:list-post', args=[topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.filter(topic=topic.id)
        self.assertEqual(response.data.get('text'), data.get('text'))
        self.assertEqual(response.data.get('text'), post.text)
        self.assertEqual(response.data.get('is_userful'), post.is_userful)
        self.assertEqual(response.data.get('author'), post.author)
        self.assertEqual(response.data.get('position'), post.position)
        self.assertEqual(response.data.get('pubdate'), post.pubdate)

    def test_failure_post_in_a_forum_we_cannot_read(self):
        """
        Tries to create a post in a private topic with a normal user.
        """
        group = Group.objects.create(name="staff")

        profile = StaffProfileFactory()
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)
        data = {
            'text': 'Welcome to this post!'
        }
        response = self.client.post(reverse('api:forum:list-post', args=(topic.pk,)), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_in_a_private_forum(self):
        """
        Post in a private topic with a user that has access right.
        """
        group = Group.objects.create(name="staff")
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)
        data = {
            'text': 'Welcome to this post!'
        }
        response = self.client_authentificated.post(reverse('api:forum:list-post', args=(topic.pk,)), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.filter(topic=topic.id)
        self.assertEqual(response.data.get('text'), data.get('text'))
        self.assertEqual(response.data.get('text'), post.text)
        self.assertEqual(response.data.get('is_userful'), post.is_userful)
        self.assertEqual(response.data.get('author'), post.author)
        self.assertEqual(response.data.get('position'), post.position)
        self.assertEqual(response.data.get('pubdate'), post.pubdate)

    def test_detail_post(self):
        """
        Gets all information about a post.
        """

        topic = self.create_topic_with_post()
        post = Post.objects.filter(topic=topic.id).first()
        response = self.client.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(post.id, response.data.get('id'))
        self.assertIsNotNone(response.data.get('text'))
        self.assertIsNone(response.data.get('text_html'))
        self.assertIsNotNone(response.data.get('pubdate'))
        self.assertIsNone(response.data.get('update'))
        self.assertEqual(post.position_in_topic, response.data.get('position_in_topic'))
        self.assertEqual(topic.author, response.data.get('author'))

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
        group = Group.objects.create(name="staff")
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, self.profile)
        post = Post.objects.filter(topic=topic.id).first()

        # Anonymous
        self.client = APIClient()
        response = self.client.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User
        response = self.client_authentificated.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        response = self.client_authentificated_staff.get(reverse('api:forum:detail-post', args=[topic.id, post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# TODO
# Lister les message d'un membre staff en étant staff
# Lister les message d'un membre staff en étant anonyme
# Lister les messages d'un membre staff en étant user

    def test_list_of_member_posts_empty(self):
        """
        Gets empty list of posts that that a specified member created.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost'), args=[self.profile.id])
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

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost'), args=[self.profile.id])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 10)
        self.assertEqual(len(response.data.get('results')), 10)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_member_posts_with_several_pages(self):
        """
        Gets list of a member topics with several pages in the database.
        """
        self.create_multiple_forums_with_topics(REST_PAGE_SIZE + 1, 1, self.profile)

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost'), args=[self.profile.id])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(len(response.data.get('results')), REST_PAGE_SIZE)

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost'), args=[self.profile.id])
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
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost')+ '?page=2', args=[self.profile.id])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_member_post_for_a_wrong_page_given(self):
        """
        Gets an error when the member posts asks a wrong page.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost') + '?page=2', args=[self.profile.id])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_member_posts_with_a_custom_page_size(self):
        """
        Gets list of user's topics with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_topic_with_post(REST_PAGE_SIZE * 2, 1, self.profile)

        page_size = 'page_size'
        response = self.client.get(reverse('api:forum:list-memberpost') + '?{}=20'.format(page_size), args=[self.profile.id])
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

        response = self.client_authenticated.get(reverse('api:forum:list-memberpost') + '?page_size={}'.format(page_size_value), args=[self.profile.id])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get('results')))

    def test_list_of_unknow_member_posts(self):
        """
        Gets empty list of posts for a member that does not exists.
        """
        response = self.client_authenticated.get(reverse('api:forum:list-memberpost'), args=[666])
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
            'text': 'There is a guy flooding about Flask, con you do something about it ?',
        }

        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-topic', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.post(reverse('api:forum:list-topic', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # VERIFIER EN BDD TODO

    def test_alert_post_in_private_forum(self):
        """
        Tries to alert a post in a public forum with different type of users
        """
        profile = StaffProfileFactory()
        group = Group.objects.create(name="staff")
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=1)
        data = {
            'text': 'There is a guy flooding about Flask, con you do something about it ?',
        }

        self.client = APIClient()
        response = self.client.post(reverse('api:forum:list-topic', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client_authenticated.post(reverse('api:forum:list-topic', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client_authenticated_staff.post(reverse('api:forum:list-topic', args=[topic.id, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # VERIFIER EN BDD TODO

    def test_alert_post_not_found(self):
        """
        Tries to alert a post in a public forum with different type of users
        """
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        post = PostFactory(topic=topic, author=profile.user, position=1)
        data = {
            'text': 'There is a guy flooding about Flask, con you do something about it ?',
        }

        response = self.client_authentificated.post(reverse('api:forum:list-topic', args=[666, post.id]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client_authentificated.post(reverse('api:forum:list-topic', args=[topic.id, 666]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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
