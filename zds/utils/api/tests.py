import os
import shutil
from copy import deepcopy

from django.conf import settings
from django.core.cache import caches
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.api.pagination import REST_MAX_PAGE_SIZE, REST_PAGE_SIZE, REST_PAGE_SIZE_QUERY_PARAM
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests.factories import PublishableContentFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["extra_content_generation_policy"] = "NOTHING"


@override_settings(ZDS_APP=overridden_zds_app)
class TagListAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_list_of_tags_empty(self):
        """
        Gets empty list of tags in the database.
        """
        response = self.client.get(reverse("api:utils:tags-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("results"), [])
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_tags(self):
        """
        Gets list of tags not empty in the database.
        """
        self.create_multiple_tags()

        response = self.client.get(reverse("api:utils:tags-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_tags_with_several_pages(self):
        """
        Gets list of tags with several pages in the database.
        """
        self.create_multiple_tags(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:utils:tags-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)

        response = self.client.get(reverse("api:utils:tags-list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))
        self.assertEqual(len(response.data.get("results")), 1)

    def test_list_of_tags_for_a_page_given(self):
        """
        Gets list of tags with several pages and gets a page different that the first one.
        """
        self.create_multiple_tags(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:utils:tags-list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 11)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))

    def test_list_of_tags_for_a_wrong_page_given(self):
        """
        Gets an error when the tag asks a wrong page.
        """
        response = self.client.get(reverse("api:utils:tags-list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_tags_with_a_custom_page_size(self):
        """
        Gets list of tags with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_tags(REST_PAGE_SIZE * 2)

        page_size = "page_size"
        response = self.client.get(reverse("api:utils:tags-list") + f"?{page_size}=20")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 20)
        self.assertEqual(len(response.data.get("results")), 20)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_tags_with_a_wrong_custom_page_size(self):
        """
        Gets list of tags with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_tags(page_size_value)

        response = self.client.get(reverse("api:utils:tags-list") + f"?page_size={page_size_value}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), page_size_value)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get("results")))

    def test_search_in_list_of_tags(self):
        """
        Gets list of tags corresponding to the value given by the search parameter.
        """
        self.create_multiple_tags()

        response = self.client.get(reverse("api:utils:tags-list") + "?search=number0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("count") > 0)

    def test_search_without_results_in_list_of_tags(self):
        """
        Gets a list empty when there are tags but which doesn't match with the search
        parameter value.
        """
        self.create_multiple_tags()

        response = self.client.get(reverse("api:utils:tags-list") + "?search=zozor")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def create_multiple_tags(self, number_of_tags=REST_PAGE_SIZE):
        tags = []
        for tag in range(0, number_of_tags):
            tags.append("number" + str(tag))

        # Prepare content containing all the tags
        content = PublishableContentFactory(type="TUTORIAL")
        content.add_tags(tags)
        content.save()
        content_draft = content.load_version()

        # then, publish it !
        publish_content(content, content_draft)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP["content"]["repo_private_path"]):
            shutil.rmtree(settings.ZDS_APP["content"]["repo_private_path"])
        if os.path.isdir(settings.ZDS_APP["content"]["repo_public_path"]):
            shutil.rmtree(settings.ZDS_APP["content"]["repo_public_path"])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
