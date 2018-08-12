from django.core.cache import caches
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_extensions.settings import extensions_api_settings

from zds.gallery.factories import UserGalleryFactory, GalleryFactory
from zds.member.factories import ProfileFactory
from zds.member.api.tests import create_oauth2_client, authenticate_client


class GalleryListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        client_oauth2 = create_oauth2_client(self.profile.user)
        authenticate_client(self.client, client_oauth2, self.profile.user.username, 'hostel77')

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_list_of_gallery_empty(self):
        response = self.client.get(reverse('api:gallery:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results'), [])
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))

    def test_list_of_gallery(self):

        gallery = GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=gallery)
        response = self.client.get(reverse('api:gallery:list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertIsNone(response.data.get('next'))
        self.assertIsNone(response.data.get('previous'))
