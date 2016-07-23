# coding: utf-8

from django.core.cache import caches
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.member.api.tests import create_oauth2_client, authenticate_client
from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory
from zds.utils.mps import send_message_mp


class NotificationListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        client_oauth2 = create_oauth2_client(self.profile.user)
        authenticate_client(self.client, client_oauth2, self.profile.user.username, 'hostel77')
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_list_of_notifications_empty(self):
        """
        Gets empty list of notifications in the database.
        """
        response = self.client.get(reverse('api:notification:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_notifications(self):
        """
        Gets list of notifications.
        """
        self.create_notification_for_pm(ProfileFactory().user, self.profile.user)
        response = self.client.get(reverse('api:notification:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_apply_filter_on_notifications(self):
        """
        Subscribe to a private topic, and gets the list of notifications with a proper
        filter, with an unsuitable filter and with an unknown filter.
        """
        self.create_notification_for_pm(ProfileFactory().user, self.profile.user)
        response = self.client.get(reverse('api:notification:list') + '?type=privatetopic')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(reverse('api:notification:list') + '?type=privatepost')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(reverse('api:notification:list') + '?type=xyz')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def create_notification_for_pm(self, sender, target):
        topic = PrivateTopicFactory(author=sender)
        topic.participants.add(target)
        send_message_mp(author=sender, n_topic=topic, text='Testing')
