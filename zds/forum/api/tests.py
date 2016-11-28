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
from zds.member.factories import ProfileFactory, StaffProfileFactory, ProfileNotSyncFactory

from zds.forum.factories import PostFactory
from zds.forum.tests.tests_views import create_category, add_topic_in_a_forum
from zds.member.factories import ProfileFactory
from zds.utils.models import CommentVote


class ForumPostKarmaAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
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
        group = Group.objects.create(name='DummyGroup_1')

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

# Lister les forums vide
# Lister les forum, 200 une seule page
# Liste des forum plusieurs page
# Lister les forums avec page size
# Lister les forums avec une page de trop 
# Liste les forums avec page size et accéder a la page deux
# Liste les forums avec un staff (on boit les forums privé)


class ForumAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        
        self.profile = ProfileFactory()
        client_oauth2 = create_oauth2_client(self.profile.user)
        client_authenticated = APIClient()
        authenticate_client(client_authenticated, client_oauth2, self.profile.user.username, 'hostel77')

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def create_multiple_forums(self, number_of_forum=REST_PAGE_SIZE):
        for forum in xrange(0, number_of_forum):
            category, forum = create_category()

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

# TODO regler le probleme de l-user admin
#done Créer un forum en étant anonyme 401
#done Créer un forum en étant membre 401
#done Créer un forum en étant staff 200
#done Creer un fórum avec un titre qui existe deja pour tester le slug
#done Creer un fórum sans categorie
#done Crrer un fórum sans titre
#done Crrer un fórum sans soustitre
#done creer un forum sans categorie
#avec titre vide/soustitre vide et categorie vide
# creer une forum dans une categorie qui n exist epas

    def test_new_forum_with_anonymous(self):
        """
        Tries to create a new forum with an anonymous (non authentified) user.
        """
        data = {
            'titre': 'Flask',
            'subtitle': 'Flask is the best framework EVER !',
            'categorie': '2'
        }
        
        self.create_multiple_forums(5)
        response = self.client.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
        
    def test_new_forum_with_user(self):
        """
        Tries to create a new forum with an user.
        """
        data = {
            'titre': 'Flask',
            'subtitle': 'Flask is the best framework EVER !',
            'categorie': '2'
        }
        
        self.create_multiple_forums(5)
        client = APIClient()
        response = client.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_new_forum_with_staff(self):
        """
        Tries to create a new forum with an staff user.
        """
        data = {
            'titre': 'Flask',
            'subtitle': 'Flask is the best framework EVER !',
            'categorie': '2'
        }

        self.create_multiple_forums(5)
        self.staff = StaffProfileFactory()
        client_oauth2 = create_oauth2_client(self.staff.user)
        self.client_authenticated_staff = APIClient()
        authenticate_client(self.client_authenticated_staff, client_oauth2, self.staff.user.username, 'hostel77')

        response = self.client_authenticated_staff.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_new_forum_slug_collision(self):
        """
        Tries to create two forums with the same title to see if the slug generated is different.
        """
        data = {
            'titre': 'Flask',
            'subtitle': 'Flask is the best framework EVER !',
            'categorie': '2'
        }

        self.create_multiple_forums(5)
        response = self.client_authenticated_staff.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response2 = self.client_authenticated_staff.post(reverse('api:forum:list'), data)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data.get('slug'), response2.data.get('slug'))
        
    def test_new_forum_without_title(self):
        """
        Tries to create a new forum with an staff user, without a title.
        """
        data = {
            'subtitle': 'Flask is the best framework EVER !',
            'categorie': '2'
        }
        
        self.create_multiple_forums(5)
        response = self.client_authenticated_staff.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_new_forum_without_subtitle(self):
        """
        Tries to create a new forum with an staff user, without a subtitle.
        """
        data = {
            'titre': 'Flask',
            'categorie': '2'
        }

        self.create_multiple_forums(5)
        response = self.client_authenticated_staff.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_new_forum_without_category(self):
        """
        Tries to create a new forum with an staff user without a category.
        """
        data = {
            'titre': 'Flask',
            'subtitle': 'Flask is the best framework EVER !',
        }

        self.create_multiple_forums(5)
        response = self.client_authenticated_staff.post(reverse('api:forum:list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



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
