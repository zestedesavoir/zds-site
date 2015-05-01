# coding: utf-8
from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from zds import settings
from zds.member.api.tests import create_oauth2_client, authenticate_client
from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.mp.models import PrivateTopic


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

    def test_list_of_private_topics_without_expand(self):
        """
        Gets list of private topics without expand parameter.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, 1)

        response = self.client.get(reverse('api-mp-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author = response.data.get('results')[0].get('author')
        self.assertEqual(author, self.profile.user.id)

    def test_expand_list_of_private_topics_for_author(self):
        """
        Gets list of private topics with author field expanded.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, 1)

        response = self.client.get(reverse('api-mp-list') + '?expand=author')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author = response.data.get('results')[0].get('author')
        self.assertIsInstance(author, OrderedDict)
        self.assertEqual(author.get('username'), self.profile.user.username)

    def test_create_private_topics_with_client_unauthenticated(self):
        """
        Creates a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.post(reverse('api-mp-list'), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_of_private_topics(self):
        """
        Creates a private topic with the current user, a title, a subtitle and a participant.
        """
        another_profile = ProfileFactory()
        data = {
            'title': 'I love ice cream!',
            'subtitle': 'Come eat one with me.',
            'participants': another_profile.user.id,
            'text': 'Welcome to this private topic!'
        }
        response = self.client.post(reverse('api-mp-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(1, len(private_topics))
        self.assertEqual(response.data.get('title'), private_topics[0].title)
        self.assertEqual(response.data.get('subtitle'), private_topics[0].subtitle)
        self.assertEqual(response.data.get('participants')[0], private_topics[0].participants.all()[0].id)
        self.assertEqual(data.get('text'), private_topics[0].last_message.text)

    def test_create_of_private_topics_without_subtitle(self):
        """
        Creates a private topic without a subtitle.
        """
        another_profile = ProfileFactory()
        data = {
            'title': 'I love ice cream!',
            'participants': another_profile.user.id,
            'text': 'Welcome to this private topic!'
        }
        response = self.client.post(reverse('api-mp-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(1, len(private_topics))
        self.assertEqual(response.data.get('title'), private_topics[0].title)
        self.assertEqual(response.data.get('subtitle'), private_topics[0].subtitle)
        self.assertEqual(response.data.get('participants')[0], private_topics[0].participants.all()[0].id)
        self.assertEqual(data.get('text'), private_topics[0].last_message.text)

    def test_create_of_private_topics_without_title(self):
        """
        Creates a private topic without a title.
        """
        another_profile = ProfileFactory()
        data = {
            'subtitle': 'Come eat one with me.',
            'participants': another_profile.user.id,
            'text': 'Welcome to this private topic!'
        }
        response = self.client.post(reverse('api-mp-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(0, len(private_topics))

    def test_create_of_private_topics_without_participants(self):
        """
        Creates a private topic without participants.
        """
        data = {
            'title': 'I love ice cream!',
            'subtitle': 'Come eat one with me.',
            'text': 'Welcome to this private topic!'
        }
        response = self.client.post(reverse('api-mp-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(0, len(private_topics))

    def test_create_of_private_topics_without_text(self):
        """
        Creates a private topic without a text.
        """
        another_profile = ProfileFactory()
        data = {
            'title': 'I love ice cream!',
            'subtitle': 'Come eat one with me.',
            'participants': another_profile.user.id,
        }
        response = self.client.post(reverse('api-mp-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(0, len(private_topics))

    def test_leave_private_topics_with_client_unauthenticated(self):
        """
        Leaves a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.delete(reverse('api-mp-list'), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_leave_private_topics(self):
        """
        Leaves private topics.
        """
        private_topics = self.create_multiple_private_topics_for_member(self.profile.user, 1)

        data = {
            'pk': private_topics[0].id
        }
        response = self.client.delete(reverse('api-mp-list'), data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=private_topics[0].id).count())

    def create_multiple_private_topics_for_member(self, user, number_of_users=settings.REST_FRAMEWORK['PAGINATE_BY']):
        return [PrivateTopicFactory(author=user) for private_topic in xrange(0, number_of_users)]


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

    def test_update_mp_details_without_any_change(self):
        """
        Updates a MP but without any changes.
        """
        response = self.client.put(reverse('api-mp-detail', args=[self.private_topic.id]), {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.private_topic.title, response.data.get('title'))
        self.assertEqual(self.private_topic.subtitle, response.data.get('subtitle'))
        self.assertEqual(self.private_topic.participants.count(), len(response.data.get('participants')))

    def test_update_mp_title(self):
        """
        Update title of a MP.
        """
        data = {
            'title': 'Do you love Tacos?'
        }
        response = self.client.put(reverse('api-mp-detail', args=[self.private_topic.id]), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('title'), data.get('title'))

    def test_update_mp_subtitle(self):
        """
        Update subtitle of a MP.
        """
        data = {
            'subtitle': 'If you don\'t love Tacos, you are weird!'
        }
        response = self.client.put(reverse('api-mp-detail', args=[self.private_topic.id]), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('subtitle'), data.get('subtitle'))

    def test_update_mp_participants(self):
        """
        Update participants of a MP.
        """
        another_profile = ProfileFactory()
        data = {
            'participants': another_profile.user.id
        }
        response = self.client.put(reverse('api-mp-detail', args=[self.private_topic.id]), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('participants')[0], data.get('participants'))

    def test_update_mp_with_client_unauthenticated(self):
        """
        Updates a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.put(reverse('api-mp-detail', args=[self.private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_a_private_topic_not_present(self):
        """
        Gets an error 404 when the private topic isn't present in the database.
        """
        response = self.client.put(reverse('api-mp-detail', args=[42]), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private topic.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)

        response = self.client.put(reverse('api-mp-detail', args=[another_private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_mp_with_client_unauthenticated(self):
        """
        Leaves a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.delete(reverse('api-mp-detail', args=[self.private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_leave_topic_no_exist(self):
        """
        Gets an error 404 when the private topic isn't present in the database.
        """
        response = self.client.delete(reverse('api-mp-detail', args=[42]), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private topic.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)

        response = self.client.delete(reverse('api-mp-detail', args=[another_private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success_leave_topic_as_author_no_participants(self):
        """
        Leaves a private topic when we are the last participant.
        """
        self.private_topic.participants.clear()
        self.private_topic.save()

        response = self.client.delete(reverse('api-mp-detail', args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=self.private_topic.id).count())

    def test_success_leave_topic_as_author(self):
        """
        Leaves a private topic when we are the author and check than a participant become the new author.
        """
        another_profile = ProfileFactory()
        self.private_topic.participants.add(another_profile.user)

        response = self.client.delete(reverse('api-mp-detail', args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(1, PrivateTopic.objects.filter(pk=self.private_topic.id).count())
        self.assertEqual(another_profile.user, PrivateTopic.objects.get(pk=self.private_topic.id).author)

    def test_success_leave_topic_as_participant(self):
        """
        Leaves a private topic when we are just in participants.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        PrivatePostFactory(author=another_profile.user, privatetopic=another_private_topic, position_in_topic=1)
        another_private_topic.participants.add(self.profile.user)

        self.assertEqual(another_profile.user, PrivateTopic.objects.get(pk=another_private_topic.id).author)
        self.assertIn(self.profile.user, PrivateTopic.objects.get(pk=another_private_topic.id).participants.all())

        response = self.client.delete(reverse('api-mp-detail', args=[another_private_topic.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(another_profile.user, PrivateTopic.objects.get(pk=another_private_topic.id).author)
        self.assertNotIn(self.profile.user, PrivateTopic.objects.get(pk=another_private_topic.id).participants.all())


class PrivatePostListAPI(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        client_oauth2 = create_oauth2_client(self.profile.user)
        authenticate_client(self.client, client_oauth2, self.profile.user.username, 'hostel77')

    def test_list_mp_with_client_unauthenticated(self):
        """
        Gets list of private posts of a private topic given with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse('api-mp-message-list', args=[0]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_of_private_posts(self):
        """
        Gets list of private posts of a member.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic)

        response = self.client.get(reverse('api-mp-message-list', args=[private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertEqual(len(response.data.get('results')), settings.REST_FRAMEWORK['PAGINATE_BY'])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_private_posts_with_several_pages(self):
        """
        Gets list of private posts of a member with several pages.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic,
                                                      settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)

        response = self.client.get(reverse('api-mp-message-list', args=[private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_private_posts_for_a_page_given(self):
        """
        Gets list of private posts with several pages and gets a page different that the first one.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic,
                                                      settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)

        response = self.client.get(reverse('api-mp-message-list', args=[private_topic.id]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_private_posts_for_a_wrong_page_given(self):
        """
        Gets an error when the user asks a wrong page.
        """
        response = self.client.get(reverse('api-mp-message-list', args=[42]) + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_private_posts_with_a_custom_page_size(self):
        """
        Gets list of private posts with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic,
                                                      settings.REST_FRAMEWORK['PAGINATE_BY'] * 2)

        page_size = 'page_size'
        response = self.client.get(reverse('api-mp-message-list', args=[private_topic.id]) + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(settings.REST_FRAMEWORK['PAGINATE_BY_PARAM'], page_size)

    def test_list_of_private_posts_with_a_wrong_custom_page_size(self):
        """
        Gets list of private posts with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = settings.REST_FRAMEWORK['MAX_PAGINATE_BY'] + 1
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, page_size_value)

        response = self.client.get(
            reverse('api-mp-message-list', args=[private_topic.id]) + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(settings.REST_FRAMEWORK['MAX_PAGINATE_BY'], len(response.data.get('results')))

    def test_list_of_private_posts_with_x_data_format_html(self):
        """
        Gets list of private posts with a Html value for X-Data-Format header.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, 1)

        response = self.client.get(reverse('api-mp-message-list', args=[private_topic.id]),
                                   **{'HTTP_X_DATA_FORMAT': 'Html'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get('results')[0].get('text_html'))
        self.assertIsNone(response.data.get('results')[0].get('text'))

    def test_list_of_private_posts_with_x_data_format_markdown(self):
        """
        Gets list of private posts with a Markdown value for X-Data-Format header.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, 1)

        response = self.client.get(reverse('api-mp-message-list', args=[private_topic.id]),
                                   **{'HTTP_X_DATA_FORMAT': 'Markdown'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get('results')[0].get('text'))
        self.assertIsNone(response.data.get('results')[0].get('text_html'))

    def create_multiple_private_posts_for_member(self, user, private_topic,
                                                 number_of_users=settings.REST_FRAMEWORK['PAGINATE_BY']):
        list = []
        for i in xrange(0, number_of_users):
            private_post = PrivatePostFactory(author=user, privatetopic=private_topic, position_in_topic=i)
            private_topic.last_message = private_post
            list.append(private_post)
        return list


class PrivatePostDetailAPI(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_post = PrivatePostFactory(author=self.profile.user, privatetopic=self.private_topic,
                                               position_in_topic=1)
        self.client = APIClient()
        client_oauth2 = create_oauth2_client(self.profile.user)
        authenticate_client(self.client, client_oauth2, self.profile.user.username, 'hostel77')

    def test_detail_private_post_with_client_unauthenticated(self):
        """
        Gets details about a private post with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(
            reverse('api-mp-message-detail', args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_private_post_with_wrong_identifiers(self):
        """
        Tries to get details of a private post in a wrong private topic.
        """
        another_private_topic = PrivateTopicFactory(author=self.profile.user)
        response = self.client.get(
            reverse('api-mp-message-detail', args=[another_private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detail_private_post_of_a_member(self):
        """
        Gets all information about a private post.
        """
        response = self.client.get(reverse('api-mp-message-detail', args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.private_post.id, response.data.get('id'))
        self.assertIsNotNone(response.data.get('text'))
        self.assertIsNone(response.data.get('text_html'))
        self.assertIsNotNone(response.data.get('pubdate'))
        self.assertIsNone(response.data.get('update'))
        self.assertEqual(self.private_post.position_in_topic, response.data.get('position_in_topic'))
        self.assertEqual(self.private_topic.id, response.data.get('privatetopic'))
        self.assertEqual(self.profile.user.id, response.data.get('author'))

    def test_detail_of_a_private_topic_not_present(self):
        """
        Gets an error 404 when the private post isn't present in the database.
        """
        response = self.client.get(reverse('api-mp-message-detail', args=[self.private_topic.id, 42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_of_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private post.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(author=self.profile.user, privatetopic=another_private_topic,
                                                  position_in_topic=1)

        response = self.client.get(
            reverse('api-mp-message-detail', args=[another_private_topic.id, another_private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
