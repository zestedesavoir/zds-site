from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.api.pagination import REST_MAX_PAGE_SIZE, REST_PAGE_SIZE, REST_PAGE_SIZE_QUERY_PARAM
from zds.api.utils import authenticate_oauth2_client
from zds.member.tests.factories import ProfileFactory, UserFactory
from zds.mp.models import PrivatePostVote, PrivateTopic
from zds.mp.tests.factories import PrivatePostFactory, PrivateTopicFactory


class PrivateTopicListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.bot_group = Group()
        self.bot_group.name = settings.ZDS_APP["member"]["bot_group"]
        self.bot_group.save()

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_list_mp_with_client_unauthenticated(self):
        """
        Gets list of private topics with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_of_private_topics_empty(self):
        """
        Gets empty list of private topics of a member.
        """
        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("results"), [])
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_private_topics(self):
        """
        Gets list of private topics of a member.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_private_topics_with_several_pages(self):
        """
        Gets list of private topics of a member with several pages.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)

        response = self.client.get(reverse("api:mp:list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))
        self.assertEqual(len(response.data.get("results")), 1)

    def test_list_of_private_topics_for_a_page_given(self):
        """
        Gets list of private topics with several pages and gets a page different that the first one.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:mp:list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 11)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))

    def test_list_of_private_topics_for_a_wrong_page_given(self):
        """
        Gets an error when the user asks a wrong page.
        """
        response = self.client.get(reverse("api:mp:list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_private_topics_with_a_custom_page_size(self):
        """
        Gets list of private topics with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, REST_PAGE_SIZE * 2)

        page_size = "page_size"
        response = self.client.get(reverse("api:mp:list") + f"?{page_size}=20")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 20)
        self.assertEqual(len(response.data.get("results")), 20)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_private_topics_with_a_wrong_custom_page_size(self):
        """
        Gets list of private topics with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_private_topics_for_member(self.profile.user, page_size_value)

        response = self.client.get(reverse("api:mp:list") + f"?page_size={page_size_value}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), page_size_value)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get("results")))

    def test_search_in_list_of_private_topics(self):
        """
        Gets list of private topics corresponding to the value given by the search parameter.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse("api:mp:list") + "?search=Mon Sujet")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("count") > 0)

    def test_search_without_results_in_list_of_private_topics(self):
        """
        Gets a list empty when there are private topics but which doesn't match with the search
        parameter value.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse("api:mp:list") + "?search=Tacos")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_ordering_list_of_private_topics_by_pubdate(self):
        """
        Gets list of private topics ordered by pubdate.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse("api:mp:list") + "?ordering=pubdate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_ordering_list_of_private_topics_by_last_message(self):
        """
        Gets list of private topics ordered by last_message.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse("api:mp:list") + "?ordering=last_message")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_ordering_list_of_private_topics_by_title(self):
        """
        Gets list of private topics ordered by last_message.
        """
        self.create_multiple_private_topics_for_member(self.profile.user)

        response = self.client.get(reverse("api:mp:list") + "?ordering=title")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_private_topics_without_expand(self):
        """
        Gets list of private topics without expand parameter.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, 1)

        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author = response.data.get("results")[0].get("author")
        self.assertEqual(author, self.profile.user.id)

    def test_expand_list_of_private_topics_for_author(self):
        """
        Gets list of private topics with author field expanded.
        """
        self.create_multiple_private_topics_for_member(self.profile.user, 1)

        response = self.client.get(reverse("api:mp:list") + "?expand=author")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author = response.data.get("results")[0].get("author")
        self.assertEqual(author.get("username"), self.profile.user.username)
        self.assertEqual(author.get("avatar_url"), self.profile.get_absolute_avatar_url())

    def test_create_private_topics_with_client_unauthenticated(self):
        """
        Creates a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.post(reverse("api:mp:list"), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_of_private_topics(self):
        """
        Creates a private topic with the current user, a title, a subtitle and a participant.
        """
        another_profile = ProfileFactory()
        data = {
            "title": "I love ice cream!",
            "subtitle": "Come eat one with me.",
            "participants": [another_profile.user.id],
            "text": "Welcome to this private topic!",
        }
        response = self.client.post(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(1, len(private_topics))
        self.assertEqual(response.data.get("title"), private_topics[0].title)
        self.assertEqual(response.data.get("subtitle"), private_topics[0].subtitle)
        self.assertEqual(response.data.get("participants")[0], private_topics[0].participants.all()[0].id)
        self.assertEqual(data.get("text"), private_topics[0].last_message.text)
        self.assertEqual(response.data.get("author"), self.profile.user.id)
        self.assertIsNotNone(response.data.get("last_message"))
        self.assertIsNotNone(response.data.get("pubdate"))

    def test_create_of_private_topics_without_subtitle(self):
        """
        Creates a private topic without a subtitle.
        """
        another_profile = ProfileFactory()
        data = {
            "title": "I love ice cream!",
            "participants": [another_profile.user.id],
            "text": "Welcome to this private topic!",
        }
        response = self.client.post(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(1, len(private_topics))
        self.assertEqual(response.data.get("title"), private_topics[0].title)
        self.assertEqual(response.data.get("subtitle"), private_topics[0].subtitle)
        self.assertEqual(response.data.get("participants")[0], private_topics[0].participants.all()[0].id)
        self.assertEqual(data.get("text"), private_topics[0].last_message.text)
        self.assertEqual(response.data.get("author"), self.profile.user.id)
        self.assertIsNotNone(response.data.get("last_message"))
        self.assertIsNotNone(response.data.get("pubdate"))

    def test_create_of_private_topics_without_title(self):
        """
        Creates a private topic without a title.
        """
        another_profile = ProfileFactory()
        data = {
            "subtitle": "Come eat one with me.",
            "participants": [another_profile.user.id],
            "text": "Welcome to this private topic!",
        }
        response = self.client.post(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(0, len(private_topics))

    def test_create_of_private_topics_without_participants(self):
        """
        Creates a private topic without participants.
        """
        data = {
            "title": "I love ice cream!",
            "subtitle": "Come eat one with me.",
            "text": "Welcome to this private topic!",
        }
        response = self.client.post(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(0, len(private_topics))

    def test_create_of_private_topics_without_text(self):
        """
        Creates a private topic without a text.
        """
        another_profile = ProfileFactory()
        data = {
            "title": "I love ice cream!",
            "subtitle": "Come eat one with me.",
            "participants": [another_profile.user.id],
        }
        response = self.client.post(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(self.profile.user.id)
        self.assertEqual(0, len(private_topics))

    def test_create_private_topic_with_unreachable_user(self):
        """
        Tries to create a new private topic with an unreachable user.
        """
        anonymous_user = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"])
        anonymous_user.groups.add(self.bot_group)
        anonymous_user.save()
        data = {
            "title": "I love ice cream!",
            "subtitle": "Come eat one with me.",
            "participants": [anonymous_user.id],
        }
        response = self.client.post(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        private_topics = PrivateTopic.objects.get_private_topics_of_user(anonymous_user.id)
        self.assertEqual(0, len(private_topics))

    def test_leave_private_topics_with_client_unauthenticated(self):
        """
        Leaves a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.delete(reverse("api:mp:list"), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_leave_private_topics(self):
        """
        Leaves private topics.
        """
        private_topics = self.create_multiple_private_topics_for_member(self.profile.user, 1)

        data = {"pk": private_topics[0].id}
        response = self.client.delete(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=private_topics[0].id).count())

    def test_leave_private_topic_where_the_user_is_not_in_participants(self):
        """
        Gets an error 403 when the user try to leave a MP where he isn't present.
        """
        another_profile = ProfileFactory()
        private_topics = self.create_multiple_private_topics_for_member(another_profile.user, 1)

        data = {"pk": private_topics[0].id}
        response = self.client.delete(reverse("api:mp:list"), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cache_invalidated_when_new_private_topic(self):
        """
        When we create a new topic, the api cache is invalidated and returns the private topic.
        """
        count = self.client.get(reverse("api:mp:list")).data.get("count")

        self.create_multiple_private_topics_for_member(self.profile.user, 1)

        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count + 1)

        private_topics = self.create_multiple_private_topics_for_member(self.profile.user, 1)

        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count + 2)

        private_topics[0].delete()

        response = self.client.get(reverse("api:mp:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count + 1)

    def create_multiple_private_topics_for_member(self, user, number_of_users=REST_PAGE_SIZE):
        return [PrivateTopicFactory(author=user) for private_topic in range(0, number_of_users)]


class PrivateTopicDetailAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=self.private_topic, position_in_topic=1
        )
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.bot_group = Group()
        self.bot_group.name = settings.ZDS_APP["member"]["bot_group"]
        self.bot_group.save()

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_detail_mp_with_client_unauthenticated(self):
        """
        Gets details about a private topic with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_of_a_member(self):
        """
        Gets all information about a private topic.
        """
        response = self.client.get(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.private_topic.id, response.data.get("id"))
        self.assertEqual(self.private_topic.title, response.data.get("title"))
        self.assertEqual(self.private_topic.subtitle, response.data.get("subtitle"))
        self.assertIsNotNone(response.data.get("pubdate"))
        self.assertEqual(self.profile.user.id, response.data.get("author"))
        self.assertEqual(self.private_post.id, response.data.get("last_message"))
        self.assertEqual([], response.data.get("participants"))

    def test_detail_of_a_private_topic_not_present(self):
        """
        Gets an error 404 when the private topic isn't present in the database.
        """
        response = self.client.get(reverse("api:mp:detail", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_of_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private topic.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)

        response = self.client.get(reverse("api:mp:detail", args=[another_private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_mp_details_without_any_change(self):
        """
        Updates a MP but without any changes.
        """
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.private_topic.title, response.data.get("title"))
        self.assertEqual(self.private_topic.subtitle, response.data.get("subtitle"))
        self.assertEqual(self.private_topic.participants.count(), len(response.data.get("participants")))

    def test_update_mp_title(self):
        """
        Update title of a MP.
        """
        data = {"title": "Do you love Tacos?"}
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("title"), data.get("title"))

    def test_update_mp_subtitle(self):
        """
        Update subtitle of a MP.
        """
        data = {"subtitle": "If you don't love Tacos, you are weird!"}
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("subtitle"), data.get("subtitle"))

    def test_update_mp_participants(self):
        """
        Update participants of a MP.
        """
        another_profile = ProfileFactory()
        data = {"participants": [another_profile.user.id]}
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("participants")[0], data.get("participants")[0])

    def test_update_mp_with_client_unauthenticated(self):
        """
        Updates a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.put(reverse("api:mp:detail", args=[self.private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_a_private_topic_not_present(self):
        """
        Gets an error 404 when the private topic isn't present in the database.
        """
        response = self.client.put(reverse("api:mp:detail", args=[42]), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private topic.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)

        response = self.client.put(reverse("api:mp:detail", args=[another_private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_private_topic_with_unreachable_user(self):
        """
        Tries to update a private topic with an unreachable user.
        """
        anonymous_user = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"])
        anonymous_user.groups.add(self.bot_group)
        anonymous_user.save()
        data = {"participants": [anonymous_user.id]}
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(str(response.data.get("participants")[0]), str(data.get("participants")[0]))
        self.assertIn(anonymous_user.username, str(response.data.get("participants")[0]))

    def test_update_private_topic_with_user_not_author(self):
        """
        Gets an error 403 when we try to update a private topic when we aren't the author.
        """
        another_profile = ProfileFactory()
        self.private_topic.participants.add(another_profile.user)

        self.client = APIClient()
        authenticate_oauth2_client(self.client, another_profile.user, "hostel77")

        data = {
            "title": "Good title",
        }
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_participant_with_an_user_not_author_of_private_topic(self):
        """
        Gets an error 403 when we try to update participants of a private topic without to be the author but in
        participants.
        """
        another_profile = ProfileFactory()
        third_profile = ProfileFactory()
        self.private_topic.participants.add(another_profile.user)

        self.client = APIClient()
        authenticate_oauth2_client(self.client, another_profile.user, "hostel77")

        data = {"participants": [third_profile.user.id]}
        response = self.client.put(reverse("api:mp:detail", args=[self.private_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_mp_with_client_unauthenticated(self):
        """
        Leaves a private topic with an unauthenticated client must fail.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.delete(reverse("api:mp:detail", args=[self.private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_leave_topic_no_exist(self):
        """
        Gets an error 404 when the private topic isn't present in the database.
        """
        response = self.client.delete(reverse("api:mp:detail", args=[42]), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_private_topic_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private topic.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)

        response = self.client.delete(reverse("api:mp:detail", args=[another_private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success_leave_topic_as_author_no_participants(self):
        """
        Leaves a private topic when we are the last participant.
        """
        self.private_topic.participants.clear()
        self.private_topic.save()

        response = self.client.delete(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=self.private_topic.id).count())

    def test_success_leave_topic_as_author(self):
        """
        Leaves a private topic when we are the author and check than a participant become the new author.
        """
        another_profile = ProfileFactory()
        self.private_topic.participants.add(another_profile.user)

        response = self.client.delete(reverse("api:mp:detail", args=[self.private_topic.id]))
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

        response = self.client.delete(reverse("api:mp:detail", args=[another_private_topic.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(another_profile.user, PrivateTopic.objects.get(pk=another_private_topic.id).author)
        self.assertNotIn(self.profile.user, PrivateTopic.objects.get(pk=another_private_topic.id).participants.all())


class PrivatePostListAPI(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_topic.participants.add(ProfileFactory().user)

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_list_mp_with_client_unauthenticated(self):
        """
        Gets list of private posts of a private topic given with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse("api:mp:message-list", args=[0]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_of_private_posts(self):
        """
        Gets list of private posts of a member.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic)

        response = self.client.get(reverse("api:mp:message-list", args=[private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_private_posts_with_several_pages(self):
        """
        Gets list of private posts of a member with several pages.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:mp:message-list", args=[private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_private_posts_for_a_page_given(self):
        """
        Gets list of private posts with several pages and gets a page different that the first one.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:mp:message-list", args=[private_topic.id]) + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 11)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))

    def test_list_of_private_posts_for_a_wrong_page_given(self):
        """
        Gets an error when the user asks a wrong page.
        """
        response = self.client.get(reverse("api:mp:message-list", args=[42]) + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_private_posts_with_a_custom_page_size(self):
        """
        Gets list of private posts with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, REST_PAGE_SIZE * 2)

        page_size = "page_size"
        response = self.client.get(reverse("api:mp:message-list", args=[private_topic.id]) + f"?{page_size}=20")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 20)
        self.assertEqual(len(response.data.get("results")), 20)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_private_posts_with_a_wrong_custom_page_size(self):
        """
        Gets list of private posts with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, page_size_value)

        response = self.client.get(
            reverse("api:mp:message-list", args=[private_topic.id]) + f"?page_size={page_size_value}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), page_size_value)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get("results")))

    def test_list_of_private_posts_with_x_data_format_html(self):
        """
        Gets list of private posts with a Html value for X-Data-Format header.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, 1)

        response = self.client.get(
            reverse("api:mp:message-list", args=[private_topic.id]), **{"HTTP_X_DATA_FORMAT": "Html"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get("results")[0].get("text_html"))
        self.assertIsNone(response.data.get("results")[0].get("text"))

    def test_list_of_private_posts_with_x_data_format_markdown(self):
        """
        Gets list of private posts with a Markdown value for X-Data-Format header.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, 1)

        response = self.client.get(
            reverse("api:mp:message-list", args=[private_topic.id]), **{"HTTP_X_DATA_FORMAT": "Markdown"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get("results")[0].get("text"))
        self.assertIsNone(response.data.get("results")[0].get("text_html"))

    def test_ordering_list_of_private_posts_by_position_in_topic(self):
        """
        Gets list of private posts ordered by position_in_topic.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, REST_PAGE_SIZE)

        response = self.client.get(
            reverse("api:mp:message-list", args=[private_topic.id]) + "?ordering=position_in_topic"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_ordering_list_of_private_posts_by_pubdate(self):
        """
        Gets list of private posts ordered by pubdate.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, REST_PAGE_SIZE)

        response = self.client.get(reverse("api:mp:message-list", args=[private_topic.id]) + "?ordering=pubdate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_ordering_list_of_private_posts_by_update(self):
        """
        Gets list of private posts ordered by update.
        """
        private_topic = PrivateTopicFactory(author=self.profile.user)
        self.create_multiple_private_posts_for_member(self.profile.user, private_topic, REST_PAGE_SIZE)

        response = self.client.get(reverse("api:mp:message-list", args=[private_topic.id]) + "?ordering=update")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def create_multiple_private_posts_for_member(self, user, private_topic, number_of_users=REST_PAGE_SIZE):
        list = []
        for i in range(0, number_of_users):
            private_post = PrivatePostFactory(author=user, privatetopic=private_topic, position_in_topic=i)
            private_topic.last_message = private_post
            list.append(private_post)
        return list

    def test_create_post_with_no_field(self):
        """
        Creates a post in a topic but not with according field.
        """
        response = self.client.post(reverse("api:mp:message-list", args=[self.private_topic.id]), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_unauthenticated(self):
        """
        Creates a post in a topic with unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.post(reverse("api:mp:message-list", args=[0]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_not_in_participants(self):
        """
        Creates a post in a topic with no authorized permission (the user is not in the allowed participants)
        """
        other_profile = ProfileFactory()
        another_topic = PrivateTopicFactory(author=other_profile.user)

        data = {"text": "Welcome to this private post!"}
        response = self.client.post(reverse("api:mp:message-list", args=[another_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_post_with_bad_topic_id(self):
        """
        Creates a post in a topic with a bad topic id
        """
        data = {"text": "Welcome to this private post!"}
        response = self.client.post(reverse("api:mp:message-list", args=[99999]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_post_in_a_private_topic_with_messages(self):
        """
        Creates a post in a private topic with existing messages.
        """
        PrivatePostFactory(author=self.profile.user, privatetopic=self.private_topic, position_in_topic=1)
        participant = ProfileFactory()
        self.private_topic.participants.add(participant.user)
        PrivatePostFactory(author=participant.user, privatetopic=self.private_topic, position_in_topic=2)

        data = {"text": "Welcome to this private post!"}
        response = self.client.post(reverse("api:mp:message-list", args=[self.private_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_post_without_any_participant(self):
        """
        Creates a post in a topic without any participant.
        """
        data = {"text": "Welcome to this private post!"}
        private_topic = PrivateTopicFactory(author=self.profile.user)
        response = self.client.post(reverse("api:mp:message-list", args=[private_topic.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PrivatePostDetailAPI(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=self.private_topic, position_in_topic=1
        )
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_detail_private_post_with_client_unauthenticated(self):
        """
        Gets details about a private post with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(
            reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_private_post_with_wrong_identifiers(self):
        """
        Tries to get details of a private post in a wrong private topic.
        """
        another_private_topic = PrivateTopicFactory(author=self.profile.user)
        response = self.client.get(
            reverse("api:mp:message-detail", args=[another_private_topic.id, self.private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_private_post_of_a_member(self):
        """
        Gets all information about a private post.
        """
        response = self.client.get(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.private_post.id, response.data.get("id"))
        self.assertIsNotNone(response.data.get("text"))
        self.assertIsNone(response.data.get("text_html"))
        self.assertIsNotNone(response.data.get("pubdate"))
        self.assertIsNone(response.data.get("update"))
        self.assertEqual(self.private_post.position_in_topic, response.data.get("position_in_topic"))
        self.assertEqual(self.private_topic.id, response.data.get("privatetopic"))
        self.assertEqual(self.profile.user.id, response.data.get("author"))

    def test_detail_of_a_private_post_not_present(self):
        """
        Gets an error 404 when the private post isn't present in the database.
        """
        response = self.client.get(reverse("api:mp:message-detail", args=[self.private_topic.id, 42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_of_private_post_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to display details about the private post.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=another_private_topic, position_in_topic=1
        )

        response = self.client.get(
            reverse("api:mp:message-detail", args=[another_private_topic.id, another_private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_private_post_with_client_unauthenticated(self):
        """
        Updates details about a private post with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.put(
            reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_of_private_post_not_in_participants(self):
        """
        Gets an error 403 when the member doesn't have permission to update details about the last private post.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=another_private_topic, position_in_topic=1
        )

        response = self.client.put(
            reverse("api:mp:message-detail", args=[another_private_topic.id, another_private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_of_private_post_not_last_one(self):
        """
        Tries to update not the last message of the private topic given.
        """
        PrivatePostFactory(author=self.profile.user, privatetopic=self.private_topic, position_in_topic=2)

        response = self.client.put(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_of_private_post_last_one_but_not_the_author(self):
        """
        Tries to update the last message but not the author of this message.
        """
        another_profile = ProfileFactory()
        another_private_post = PrivatePostFactory(
            author=another_profile.user, privatetopic=self.private_topic, position_in_topic=2
        )

        response = self.client.put(
            reverse("api:mp:message-detail", args=[self.private_topic.id, another_private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_of_private_post_without_text(self):
        """
        Tries to update the last message without a new text.
        """
        response = self.client.put(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_of_private_post_success(self):
        """
        Updates the last message of a private topic.
        """
        data = {"text": "A new text"}
        response = self.client.put(
            reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("text"), data.get("text"))

    def test_update_of_private_post_success_with_special_characters(self):
        """
        Updates the last message of a private topic with special characters.
        """
        data = {"text": "éèîïà|ç&$*?!æ"}
        response = self.client.put(
            reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("text"), data.get("text"))


class PrivateTopicUnreadListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.another_profile = ProfileFactory()
        self.another_client = APIClient()
        authenticate_oauth2_client(self.another_client, self.another_profile.user, "hostel77")

        self.bot_group = Group()
        self.bot_group.name = settings.ZDS_APP["member"]["bot_group"]
        self.bot_group.save()

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_list_mp_unread_with_client_unauthenticated(self):
        """
        Gets list of private topics unread with an unauthenticated client.
        """
        client_unauthenticated = APIClient()
        response = client_unauthenticated.get(reverse("api:mp:list-unread"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_of_private_topics_unread_empty(self):
        """
        Gets empty list of private topics unread of a member.
        """
        response = self.client.get(reverse("api:mp:list-unread"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("results"), [])
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_private_topics_unread(self):
        """
        Gets list of private topics unread of a member.
        """
        private_topic = PrivateTopicFactory(author=self.another_profile.user)
        PrivatePostFactory(author=self.another_profile.user, privatetopic=private_topic, position_in_topic=1)
        private_topic.add_participant(self.profile.user)
        private_topic.save()

        response = self.client.get(reverse("api:mp:list-unread"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))


class PermissionMemberAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=self.private_topic, position_in_topic=1
        )

        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

    def test_has_read_permission_for_authenticated_users(self):
        """
        Authenticated users have permission to read PM.
        """
        response = self.client.get(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("read"))

    def test_has_write_permission_for_authenticated_users(self):
        """
        Authenticated users have permission to write PM.
        """
        response = self.client.get(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("write"))

    def test_has_update_permission_for_authenticated_users_and_author(self):
        """
        Authenticated users have permission to update PM.
        """
        response = self.client.get(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("update"))

    def test_has_not_update_permission_for_authenticated_users_and_but_not_author(self):
        """
        Authenticated users have permission to update PM.
        """
        another_profile = ProfileFactory()
        self.private_topic.participants.add(another_profile.user)

        authenticate_oauth2_client(self.client, another_profile.user, "hostel77")
        response = self.client.get(reverse("api:mp:detail", args=[self.private_topic.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("update"))

    def test_has_read_permission_for_authenticated_users_for_post(self):
        """
        Authenticated users have permission to read messages of PM.
        """
        response = self.client.get(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("read"))

    def test_has_write_permission_for_authenticated_users_for_post(self):
        """
        Authenticated users have permission to write messages of PM.
        """
        response = self.client.get(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("write"))

    def test_has_update_permission_for_authenticated_users_and_author_for_post(self):
        """
        Authenticated users have permission to update messages of PM.
        """
        response = self.client.get(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("update"))

    def test_has_not_update_permission_for_authenticated_users_and_but_not_author_for_post(self):
        """
        Authenticated users have permission to update messages of PM.
        """
        another_profile = ProfileFactory()
        self.private_topic.participants.add(another_profile.user)

        authenticate_oauth2_client(self.client, another_profile.user, "hostel77")
        response = self.client.get(reverse("api:mp:message-detail", args=[self.private_topic.id, self.private_post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("update"))


class PrivateTopicKarmaAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.private_topic = PrivateTopicFactory(author=self.profile.user)
        self.private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=self.private_topic, position_in_topic=1
        )
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_karma_of_private_post_not_in_participants(self):
        """
        Gets an error 404 when the member doesn't have permission to display karma about the private post.
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(
            author=self.profile.user, privatetopic=another_private_topic, position_in_topic=1
        )

        response = self.client.get(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, another_private_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_like_on_private_post(self):
        """
        Add thumbs up to private post
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(
            author=another_profile.user, privatetopic=another_private_topic, position_in_topic=1
        )
        another_private_topic.participants.add(self.profile.user)

        response = self.client.put(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, another_private_post.id]),
            {"vote": "like"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            PrivatePostVote.objects.filter(
                user=self.profile.user, private_post=another_private_post, positive=True
            ).exists()
        )

    def test_dislike_on_private_post(self):
        """
        Add thumbs down to private post
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(
            author=another_profile.user, privatetopic=another_private_topic, position_in_topic=1
        )
        another_private_topic.participants.add(self.profile.user)

        response = self.client.put(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, another_private_post.id]),
            {"vote": "dislike"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            PrivatePostVote.objects.filter(
                user=self.profile.user, private_post=another_private_post, positive=False
            ).exists()
        )

    def test_like_then_cancel_on_private_post(self):
        """
        Add thumbs up to private post then cancels it
        """
        another_profile = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile.user)
        another_private_post = PrivatePostFactory(
            author=another_profile.user, privatetopic=another_private_topic, position_in_topic=1
        )
        another_private_topic.participants.add(self.profile.user)

        response = self.client.put(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, another_private_post.id]),
            {"vote": "like"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, another_private_post.id]),
            {"vote": "neutral"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            PrivatePostVote.objects.filter(
                user=self.profile.user, private_post=another_private_post, positive=True
            ).exists()
        )

    def test_get_private_post_voters(self):
        """
        Verify that likes and dislikes voters can be retrieved
        """
        another_profile1 = ProfileFactory()
        another_profile2 = ProfileFactory()
        another_private_topic = PrivateTopicFactory(author=another_profile1.user)
        another_private_topic.participants.add(self.profile.user)
        another_private_topic.participants.add(another_profile2.user)

        upvoted_post = PrivatePostFactory(
            author=another_profile1.user, privatetopic=another_private_topic, position_in_topic=1, like=2
        )
        PrivatePostVote.objects.create(user=self.profile.user, private_post=upvoted_post, positive=True)
        PrivatePostVote.objects.create(user=another_profile2.user, private_post=upvoted_post, positive=True)

        downvoted_post = PrivatePostFactory(
            author=another_profile1.user, privatetopic=another_private_topic, position_in_topic=2, dislike=2
        )
        PrivatePostVote.objects.create(user=self.profile.user, private_post=downvoted_post, positive=False)
        PrivatePostVote.objects.create(user=another_profile2.user, private_post=downvoted_post, positive=False)

        neutral_post = PrivatePostFactory(
            author=another_profile1.user, privatetopic=another_private_topic, position_in_topic=3, like=1, dislike=1
        )
        PrivatePostVote.objects.create(user=self.profile.user, private_post=neutral_post, positive=True)
        PrivatePostVote.objects.create(user=another_profile2.user, private_post=neutral_post, positive=False)

        response = self.client.get(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, upvoted_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data["like"]["users"]))
        self.assertEqual(0, len(response.data["dislike"]["users"]))
        self.assertEqual(2, response.data["like"]["count"])
        self.assertEqual(0, response.data["dislike"]["count"])

        response = self.client.get(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, downvoted_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data["like"]["users"]))
        self.assertEqual(2, len(response.data["dislike"]["users"]))
        self.assertEqual(0, response.data["like"]["count"])
        self.assertEqual(2, response.data["dislike"]["count"])

        response = self.client.get(
            reverse("api:mp:mp-reaction-karma", args=[another_private_topic.id, neutral_post.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data["like"]["users"]))
        self.assertEqual(1, len(response.data["dislike"]["users"]))
        self.assertEqual(1, response.data["like"]["count"])
        self.assertEqual(1, response.data["dislike"]["count"])
