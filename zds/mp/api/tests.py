# coding: utf-8

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from zds import settings
from zds.member.api.tests import create_oauth2_client, authenticate_client
from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory


overrided_drf = settings.REST_FRAMEWORK
overrided_drf['MAX_PAGINATE_BY'] = 20


@override_settings(REST_FRAMEWORK=overrided_drf)
class PrivateTopicListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        client_oauth2 = create_oauth2_client(self.profile.user)
        authenticate_client(self.client, client_oauth2, self.profile.user.username, 'hostel77')

    def test_list_mp_with_client_unauthenticated(self):
        """
        Gets list of private topics with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse('api-mp-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_of_private_topics_empty(self):
        """
        Gets empty list of private topics of a member.
        """
        response = self.client.get(reverse('api-mp-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_private_topics(self):
        """
        Gets list of private topics of a member.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse('api-mp-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertEqual(len(response.data.get('results')), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_private_topics_with_several_pages(self):
        """
        Gets list of private topics of a member with several pages.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)

        response = self.client.get(reverse('api-mp-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_private_topics_for_a_page_given(self):
        """
        Gets list of private topics with several pages and gets a page different that the first one.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)

        response = self.client.get(reverse('api-mp-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_private_topics_for_a_wrong_page_given(self):
        """
        Gets an error when the user asks a wrong page.
        """
        response = self.client.get(reverse('api-mp-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_private_topics_with_a_custom_page_size(self):
        """
        Gets list of private topics with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, settings.REST_FRAMEWORK['PAGINATE_BY'] * 2)

        page_size = 'page_size'
        response = self.client.get(reverse('api-mp-list') + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(settings.REST_FRAMEWORK['PAGINATE_BY_PARAM'], page_size)

    def test_list_of_private_topics_with_a_wrong_custom_page_size(self):
        """
        Gets list of private topics with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = settings.REST_FRAMEWORK['MAX_PAGINATE_BY'] + 1
        self.create_multiple_private_topics_for_member(self.profile.user, page_size_value)

        response = self.client.get(reverse('api-mp-list') + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(settings.REST_FRAMEWORK['MAX_PAGINATE_BY'], len(response.data.get('results')))

    def test_search_in_list_of_private_topics(self):
        """
        Gets list of private topics corresponding to the value given by the search parameter.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse('api-mp-list') + '?search=Mon Sujet')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('count') > 0)

    def test_search_without_results_in_list_of_private_topics(self):
        """
        Gets a list empty when there are private topics but which doesn't match with the search
        parameter value.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse('api-mp-list') + '?search=Tacos')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_ordering_list_of_private_topics_by_pubdate(self):
        """
        Gets list of private topics ordered by pubdate.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse('api-mp-list') + '?ordering=pubdate')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_ordering_list_of_private_topics_by_last_message(self):
        """
        Gets list of private topics ordered by last_message.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse('api-mp-list') + '?ordering=last_message')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_ordering_list_of_private_topics_by_title(self):
        """
        Gets list of private topics ordered by last_message.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse('api-mp-list') + '?ordering=title')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def create_multiple_private_topics_for_member(self, user, number_of_users=settings.REST_FRAMEWORK['PAGINATE_BY']):
        for private_topic in xrange(0, number_of_users):
            PrivateTopicFactory(author=user)


class PrivateTopicDetailAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_post = PrivatePostFactory(author=self.profile.user, privatetopic=self.private_topic,
                                               position_in_topic=1)
        self.client = APIClient()
        client_oauth2 = create_oauth2_client(self.profile.user)
        authenticate_client(self.client, client_oauth2, self.profile.user.username, 'hostel77')

    def test_detail_mp_with_client_unauthenticated(self):
        """
        Gets details about a private topic with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse('api-mp-detail', args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_of_a_member(self):
        """
        Gets all information about a private topic.
        """
        response = self.client.get(reverse('api-mp-detail', args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.private_topic.id, response.data.get('id'))
        self.assertEqual(self.private_topic.title, response.data.get('title'))
        self.assertEqual(self.private_topic.subtitle, response.data.get('subtitle'))
        self.assertIsNotNone(response.data.get('pubdate'))
        self.assertEqual(self.profile.user.id, response.data.get('author'))
        self.assertEqual(self.private_post.id, response.data.get('last_message'))
        self.assertEqual([], response.data.get('participants'))

    def test_detail_of_a_private_topic_not_present(self):
        """
        Gets an error 404 when the private topic isn't present in the database.
        """
        response = self.client.get(reverse('api-mp-detail', args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_of_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private topic.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)

        response = self.client.get(reverse('api-mp-detail', args=[another_private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
