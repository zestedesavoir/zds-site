# coding: utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import APIClient

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.member.models import TokenRegister


overrided_drf = settings.REST_FRAMEWORK
overrided_drf['MAX_PAGINATE_BY'] = 20


@override_settings(REST_FRAMEWORK=overrided_drf)
class MemberListAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_of_users_empty(self):
        """
        Gets empty list of users in the database.
        """
        response = self.client.get(reverse('api-member-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_users(self):
        """
        Gets list of users not empty in the database.
        """
        self.create_multiple_users()

        response = self.client.get(reverse('api-member-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 10)
        self.assertEqual(len(response.data.get('results')), 10)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_users_with_several_pages(self):
        """
        Gets list of users with several pages in the database.
        """
        self.create_multiple_users(settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)

        response = self.client.get(reverse('api-member-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_users_for_a_page_given(self):
        """
        Gets list of users with several pages and gets a page different that the first one.
        """
        self.create_multiple_users(settings.REST_FRAMEWORK['PAGINATE_BY'] + 1)

        response = self.client.get(reverse('api-member-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 11)
        self.assertEqual(len(response.data.get('results')), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_list_of_users_for_a_wrong_page_given(self):
        """
        Gets an error when the user asks a wrong page.
        """
        response = self.client.get(reverse('api-member-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_users_with_a_custom_page_size(self):
        """
        Gets list of users with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_users(settings.REST_FRAMEWORK['PAGINATE_BY'] * 2)

        page_size = 'page_size'
        response = self.client.get(reverse('api-member-list') + '?{}=20'.format(page_size))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 20)
        self.assertEqual(len(response.data.get('results')), 20)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(settings.REST_FRAMEWORK['PAGINATE_BY_PARAM'], page_size)

    def test_list_of_users_with_a_wrong_custom_page_size(self):
        """
        Gets list of users with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = settings.REST_FRAMEWORK['MAX_PAGINATE_BY'] + 1
        self.create_multiple_users(page_size_value)

        response = self.client.get(reverse('api-member-list') + '?page_size={}'.format(page_size_value))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), page_size_value)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
        self.assertEqual(settings.REST_FRAMEWORK['MAX_PAGINATE_BY'], len(response.data.get('results')))

    def test_search_in_list_of_users(self):
        """
        Gets list of users corresponding to the value given by the search parameter.
        """
        self.create_multiple_users()
        StaffProfileFactory()

        response = self.client.get(reverse('api-member-list') + '?search=firmstaff')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_search_without_results_in_list_of_users(self):
        """
        Gets a list empty when there are users but which doesn't match with the search
        parameter value.
        """
        self.create_multiple_users()

        response = self.client.get(reverse('api-member-list') + '?search=zozor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_register_new_user(self):
        """
        Registers a new user in the database.
        """
        data = {
            'username': 'Clem',
            'email': 'clem@zestedesavoir.com',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('username'), data.get('username'))
        self.assertEqual(response.data.get('email'), data.get('email'))
        self.assertNotEqual(response.data.get('password'), data.get('password'))

    def test_register_two_same_users(self):
        """
        Tries to register a user two times.
        """
        data = {
            'username': 'Clem',
            'email': 'clem@zestedesavoir.com',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('username'))
        self.assertIsNotNone(response.data.get('email'))

    def test_register_new_user_without_username(self):
        """
        Tries to register a new user in the database without an username.
        """
        data = {
            'email': 'clem@zestedesavoir.com',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('username'))

    def test_register_new_user_without_email(self):
        """
        Tries to register a new user in the database without an email.
        """
        data = {
            'username': 'Clem',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('email'))

    def test_register_new_user_without_password(self):
        """
        Tries to register a new user in the database without a password.
        """
        data = {
            'username': 'Clem',
            'email': 'clem@zestedesavoir.com'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('password'))

    def test_register_new_user_is_inactive(self):
        """
        Registers a new user and checks that the user is inactive in the database.
        """
        data = {
            'username': 'Clem',
            'email': 'clem@zestedesavoir.com',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=response.data.get('username'))
        self.assertFalse(user.is_active)

    def test_register_new_user_send_an_email_to_confirm_registration(self):
        """
        Registers a new user send an email in the inbox of the target user to confirm
        his registration.
        """
        data = {
            'username': 'Clem',
            'email': 'clem@zestedesavoir.com',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEquals(len(mail.outbox), 1)

    def test_register_new_user_create_a_token(self):
        """
        Registers a new user create a token used to confirm the registration of the
        future user.
        """
        data = {
            'username': 'Clem',
            'email': 'clem@zestedesavoir.com',
            'password': 'azerty'
        }
        response = self.client.post(reverse('api-member-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=response.data.get('username'))
        token = TokenRegister.objects.get(user=user)
        self.assertIsNotNone(token)

    def test_member_list_url_with_put_method(self):
        response = self.client.put(reverse('api-member-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def create_multiple_users(self, number_of_users=settings.REST_FRAMEWORK['PAGINATE_BY']):
        for user in xrange(0, number_of_users):
            ProfileFactory()
