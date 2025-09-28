from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail
from django.core.cache import caches
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.api.pagination import REST_MAX_PAGE_SIZE, REST_PAGE_SIZE, REST_PAGE_SIZE_QUERY_PARAM
from zds.api.utils import authenticate_oauth2_client
from zds.member.models import BannedEmailProvider, TokenRegister
from zds.member.tests.factories import ProfileFactory, ProfileNotSyncFactory, StaffProfileFactory


class MemberListAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()
        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()

    def test_list_of_users_empty(self):
        """
        Gets empty list of users in the database.
        """
        response = self.client.get(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("results"), [])
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_users(self):
        """
        Gets list of users not empty in the database.
        """
        self.create_multiple_users()

        response = self.client.get(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE)
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_list_of_users_with_several_pages(self):
        """
        Gets list of users with several pages in the database.
        """
        self.create_multiple_users(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(len(response.data.get("results")), REST_PAGE_SIZE)

        response = self.client.get(reverse("api:member:list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), REST_PAGE_SIZE + 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))
        self.assertEqual(len(response.data.get("results")), 1)

    def test_list_of_users_for_a_page_given(self):
        """
        Gets list of users with several pages and gets a page different that the first one.
        """
        self.create_multiple_users(REST_PAGE_SIZE + 1)

        response = self.client.get(reverse("api:member:list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 11)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))

    def test_list_of_users_for_a_wrong_page_given(self):
        """
        Gets an error when the user asks a wrong page.
        """
        response = self.client.get(reverse("api:member:list") + "?page=2")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_of_users_with_a_custom_page_size(self):
        """
        Gets list of users with a custom page size. DRF allows to specify a custom
        size for the pagination.
        """
        self.create_multiple_users(REST_PAGE_SIZE * 2)

        page_size = "page_size"
        response = self.client.get(reverse("api:member:list") + f"?{page_size}=20")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 20)
        self.assertEqual(len(response.data.get("results")), 20)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_PAGE_SIZE_QUERY_PARAM, page_size)

    def test_list_of_users_with_a_wrong_custom_page_size(self):
        """
        Gets list of users with a custom page size but not good according to the
        value in settings.
        """
        page_size_value = REST_MAX_PAGE_SIZE + 1
        self.create_multiple_users(page_size_value)

        response = self.client.get(reverse("api:member:list") + f"?page_size={page_size_value}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), page_size_value)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))
        self.assertEqual(REST_MAX_PAGE_SIZE, len(response.data.get("results")))

    def test_search_in_list_of_users(self):
        """
        Gets list of users corresponding to the value given by the search parameter.
        """
        self.create_multiple_users()
        StaffProfileFactory()

        response = self.client.get(reverse("api:member:list") + "?search=firmstaff")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("count") > 0)

    def test_search_without_results_in_list_of_users(self):
        """
        Gets a list empty when there are users but which doesn't match with the search
        parameter value.
        """
        self.create_multiple_users()

        response = self.client.get(reverse("api:member:list") + "?search=zozor")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_search_with_results_in_right_order(self):
        """
        Gets list of users corresponding to part of a username and
        verifies that this list is in the right order, which is:
        1. "is equal" case sensitive
        2. "is equal" ignoring the case
        3. "starts with" case sensitive
        4. "starts with" ignoring the case
        5. "contains" case sensitive
        6. "contains" ignoring the case

        The test also checks that:
        - usernames containing letters of the searched word (here: 'a', 'n', 'd' and 'r')
          but NOT the searched word ("andr") are not returned
        - usernames containing non-ascii letters (eg with accents) can be returned as well
        """
        for username in ("pierre", "andr", "Radon", "alexandre", "MisterAndrew", "andré", "dragon", "Andromède"):
            ProfileFactory(user__username=username)

        response = self.client.get(reverse("api:member:list") + "?search=Andr")
        list_of_usernames = [item.get("username") for item in response.data.get("results")]
        self.assertEqual(list_of_usernames, ["andr", "Andromède", "andré", "MisterAndrew", "alexandre"])

    def test_register_new_user(self):
        """
        Registers a new user in the database.
        """
        data = {"username": "Clem", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("username"), data.get("username"))
        self.assertEqual(response.data.get("email"), data.get("email"))
        self.assertNotEqual(response.data.get("password"), data.get("password"))

    def test_register_two_same_users(self):
        """
        Tries to register a user two times.
        """
        data = {"username": "Clem", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("username"))
        self.assertIsNotNone(response.data.get("email"))

    def test_register_new_user_without_username(self):
        """
        Tries to register a new user in the database without a username.
        """
        data = {"email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("username"))

    def test_register_new_user_with_username_empty(self):
        """
        Tries to register a new user in the database with a username empty.
        """
        data = {"username": "", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("username"))

    def test_register_new_user_with_comma_in_username(self):
        """
        Tries to register a new user in the database with comma in username.
        """
        data = {"username": "Cle,m", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("username"))

    def test_register_new_user_with_username_start_and_end_with_space(self):
        """
        Tries to register a new user in the database with space at the start
        and end of the username.
        """
        data = {"username": " Clem ", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_new_user_without_email(self):
        """
        Tries to register a new user in the database without an email.
        """
        data = {"username": "Clem", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("email"))

    def test_register_new_user_with_forbidden_email(self):
        """
        Gets an error when the user tries to register a new user with a forbidden email.
        """
        moderator = StaffProfileFactory().user
        if not BannedEmailProvider.objects.filter(provider="yopmail.com").exists():
            BannedEmailProvider.objects.create(provider="yopmail.com", moderator=moderator)
        data = {"username": "Clem", "email": "clem@yopmail.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("email"))

    def test_register_new_user_without_password(self):
        """
        Tries to register a new user in the database without a password.
        """
        data = {"username": "Clem", "email": "clem@zestedesavoir.com"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get("password"))

    def test_register_new_user_is_inactive(self):
        """
        Registers a new user and checks that the user is inactive in the database.
        """
        data = {"username": "Clem", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=response.data.get("username"))
        self.assertFalse(user.is_active)

    def test_register_new_user_send_an_email_to_confirm_registration(self):
        """
        Registers a new user send an email in the inbox of the target user to confirm
        his registration.
        """
        data = {"username": "Clem", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(mail.outbox), 1)

    def test_register_new_user_create_a_token(self):
        """
        Registers a new user create a token used to confirm the registration of the
        future user.
        """
        data = {"username": "Clem", "email": "clem@zestedesavoir.com", "password": "azerty"}
        response = self.client.post(reverse("api:member:list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=response.data.get("username"))
        token = TokenRegister.objects.get(user=user)
        self.assertIsNotNone(token)

    def test_member_list_url_with_put_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.put(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_member_list_url_with_delete_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.delete(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def create_multiple_users(self, number_of_users=REST_PAGE_SIZE):
        for user in range(0, number_of_users):
            ProfileFactory()


class MemberExistsAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()
        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()

    def test_list_of_users_empty(self):
        """
        Gets empty list of users in the database.
        """
        response = self.client.get(reverse("api:member:exists"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("results"), [])
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_search_in_list_of_users(self):
        """
        Gets list of users corresponding to the value given by the search parameter.
        """
        self.create_multiple_users()
        StaffProfileFactory()

        # get a username
        response = self.client.get(reverse("api:member:list") + "?search=firmstaff")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        username = response.data["results"][0]["username"]

        response = self.client.get(reverse("api:member:exists") + "?search=" + username)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("count") > 0)

    def test_search_without_results_in_list_of_users(self):
        """
        Gets a list empty when there are users but which doesn't match with the search
        parameter value.
        """
        self.create_multiple_users()

        response = self.client.get(reverse("api:member:exists") + "?search=zozor")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get("count"), 0)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_member_list_url_with_put_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.put(reverse("api:member:exists"))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_member_list_url_with_post_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.post(reverse("api:member:exists"))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_member_list_url_with_delete_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.delete(reverse("api:member:exists"))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def create_multiple_users(self, number_of_users=REST_PAGE_SIZE):
        for user in range(0, number_of_users):
            ProfileFactory()


class MemberMyDetailAPITest(APITestCase):
    def setUp(self):
        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_detail_of_the_member(self):
        """
        Gets all information about the user.
        """
        profile = ProfileFactory()
        client_authenticated = APIClient()
        authenticate_oauth2_client(client_authenticated, profile.user, "hostel77")

        response = client_authenticated.get(reverse("api:member:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.user.id, response.data.get("id"))
        self.assertEqual(profile.user.username, response.data.get("username"))
        self.assertEqual(profile.user.email, response.data.get("email"))
        self.assertEqual(profile.user.is_active, response.data.get("is_active"))
        self.assertIsNotNone(response.data.get("date_joined"))
        self.assertEqual(profile.site, response.data.get("site"))
        self.assertEqual(profile.get_absolute_avatar_url(), response.data.get("avatar_url"))
        self.assertEqual(profile.biography, response.data.get("biography"))
        self.assertEqual(profile.sign, response.data.get("sign"))
        self.assertFalse(response.data.get("show_email"))
        self.assertEqual(profile.show_sign, response.data.get("show_sign"))
        self.assertEqual(profile.hide_forum_activity, response.data.get("hide_forum_activity"))
        self.assertEqual(profile.is_hover_enabled, response.data.get("is_hover_enabled"))
        self.assertEqual(profile.allow_temp_visual_changes, response.data.get("allow_temp_visual_changes"))
        self.assertEqual(profile.email_for_answer, response.data.get("email_for_answer"))

    def test_detail_of_the_member_not_authenticated(self):
        """
        Tries to get profile of the member with a client not authenticated.
        """
        client = APIClient()

        response = client.get(reverse("api:member:profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MemberDetailAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile = ProfileFactory()

        self.client_authenticated = APIClient()
        authenticate_oauth2_client(self.client_authenticated, self.profile.user, "hostel77")

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_detail_of_a_member(self):
        """
        Gets all information about a user.
        """
        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.profile.user.id, response.data.get("id"))
        self.assertEqual(self.profile.user.username, response.data.get("username"))
        self.assertIsNone(response.data.get("email"))
        self.assertEqual(self.profile.user.is_active, response.data.get("is_active"))
        self.assertIsNotNone(response.data.get("date_joined"))
        self.assertEqual(self.profile.site, response.data.get("site"))
        self.assertEqual(self.profile.get_absolute_avatar_url(), response.data.get("avatar_url"))
        self.assertEqual(self.profile.biography, response.data.get("biography"))
        self.assertEqual(self.profile.sign, response.data.get("sign"))
        self.assertFalse(response.data.get("show_email"))
        self.assertEqual(self.profile.show_sign, response.data.get("show_sign"))
        self.assertEqual(self.profile.hide_forum_activity, response.data.get("hide_forum_activity"))
        self.assertEqual(self.profile.is_hover_enabled, response.data.get("is_hover_enabled"))
        self.assertEqual(self.profile.email_for_answer, response.data.get("email_for_answer"))

    def test_detail_with_user_not_synchronized(self):
        """
        Gets all information about a user not synchronized.
        """
        decal = ProfileNotSyncFactory()
        response = self.client.get(reverse("api:member:detail", args=[decal.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), decal.user.id)

    def test_detail_of_a_member_who_accepts_to_show_his_email(self):
        """
        Gets all information about a user but not his email because the request isn't authenticated.
        """
        self.profile.show_email = True
        self.profile.save()

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get("email"))

    def test_detail_of_a_member_who_accepts_to_show_his_email_with_authenticated_request(self):
        """
        Gets all information about a user and his email.
        """
        self.profile.show_email = True
        self.profile.save()

        response = self.client_authenticated.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("show_email"))
        self.assertEqual(self.profile.user.email, response.data.get("email"))

    def test_detail_of_a_member_not_present(self):
        """
        Gets an error when the user isn't present in the database.
        """
        response = self.client.get(reverse("api:member:detail", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_member_details_without_any_change(self):
        """
        Updates a member but without any changes.
        """
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.profile.user.id, response.data.get("id"))
        self.assertEqual(self.profile.user.username, response.data.get("username"))
        self.assertEqual(self.profile.user.email, response.data.get("email"))
        self.assertEqual(self.profile.user.is_active, response.data.get("is_active"))
        self.assertIsNotNone(response.data.get("date_joined"))
        self.assertEqual(self.profile.site, response.data.get("site"))
        self.assertEqual(self.profile.avatar_url, response.data.get("avatar_url"))
        self.assertEqual(self.profile.biography, response.data.get("biography"))
        self.assertEqual(self.profile.sign, response.data.get("sign"))
        self.assertFalse(response.data.get("show_email"))
        self.assertEqual(self.profile.show_sign, response.data.get("show_sign"))
        self.assertEqual(self.profile.hide_forum_activity, response.data.get("hide_forum_activity"))
        self.assertEqual(self.profile.is_hover_enabled, response.data.get("is_hover_enabled"))
        self.assertEqual(self.profile.email_for_answer, response.data.get("email_for_answer"))

    def test_update_member_details_with_user_not_synchronized(self):
        """
        Updates a member of a user not synchronized.
        """
        decal = ProfileNotSyncFactory()

        client_authenticated = APIClient()
        authenticate_oauth2_client(client_authenticated, decal.user, "hostel77")

        response = client_authenticated.put(reverse("api:member:detail", args=[decal.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), decal.user.id)

    def test_update_member_details_not_exist(self):
        """
        Tries to update a member who doesn't exist in the database.
        """
        response = self.client_authenticated.put(reverse("api:member:detail", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_member_details_with_a_problem_in_authentication(self):
        """
        Tries to update a member with a authentication not valid.
        """
        response = self.client.put(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_member_details_without_permissions(self):
        """
        Tries to update information about a member when the user isn't the target user.
        """
        another = ProfileFactory()
        response = self.client_authenticated.put(reverse("api:member:detail", args=[another.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_member_details_username(self):
        """
        Updates username of a member given.
        """
        data = {"username": "Clem"}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), data.get("username"))

    def test_update_member_details_email(self):
        """
        Updates email of a member given.
        """
        data = {"email": "clem@zestedesavoir.com"}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email"), data.get("email"))

    def test_update_member_details_with_email_malformed(self):
        """
        Gets an error when the user try to update a member given with an email malformed.
        """
        data = {"email": "wrong email"}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_member_details_site(self):
        """
        Updates site of a member given.
        """
        data = {"site": "www.zestedesavoir.com"}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("site"), data.get("site"))

    def test_update_member_details_avatar(self):
        """
        Updates url of the member's avatar given.
        """
        data = {"avatar_url": "www.zestedesavoir.com"}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("avatar_url"), data.get("avatar_url"))

    def test_update_member_details_biography(self):
        """
        Updates biography of a member given.
        """
        data = {"biography": "It is my awesome biography."}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("biography"), data.get("biography"))

    def test_update_member_details_sign(self):
        """
        Updates sign of a member given.
        """
        data = {"sign": "It is my awesome sign."}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("sign"), data.get("sign"))

    def test_update_member_details_show_email(self):
        """
        Updates show email of a member given.
        """
        data = {"show_email": True}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("show_email"), data.get("show_email"))

        data = {"show_email": False}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("show_email"), data.get("show_email"))

    def test_update_member_details_show_sign(self):
        """
        Updates show sign of a member given.
        """
        data = {"show_sign": True}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("show_sign"), data.get("show_sign"))

        data = {"show_sign": False}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("show_sign"), data.get("show_sign"))

    def test_update_member_details_hide_forum_activity(self):
        """
        Updates Hide Comment Activity of a given member.
        """
        data = {"hide_forum_activity": True}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("hide_forum_activity"), data.get("hide_forum_activity"))

        data = {"hide_forum_activity": False}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("hide_forum_activity"), data.get("hide_forum_activity"))

    def test_update_member_details_is_hover_enabled(self):
        """
        Updates hover or click of a member given.
        """
        data = {"is_hover_enabled": True}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("is_hover_enabled"), data.get("is_hover_enabled"))

        data = {"is_hover_enabled": False}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("is_hover_enabled"), data.get("is_hover_enabled"))

    def test_update_member_details_email_for_answer(self):
        """
        Updates email for answer of a member given.
        """
        data = {"email_for_answer": True}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email_for_answer"), data.get("email_for_answer"))

        data = {"email_for_answer": False}
        response = self.client_authenticated.put(reverse("api:member:detail", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email_for_answer"), data.get("email_for_answer"))

    def test_member_detail_url_with_post_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.post(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_member_detail_url_with_delete_method(self):
        """
        Gets an error when the user try to make a request with a method not allowed.
        """
        response = self.client.delete(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class MemberDetailReadingOnlyAPITest(APITestCase):
    def setUp(self):
        self.mas = ProfileFactory()
        settings.ZDS_APP["member"]["bot_account"] = self.mas.user.username

        self.profile = ProfileFactory()
        self.staff = StaffProfileFactory()
        self.client_authenticated = APIClient()
        authenticate_oauth2_client(self.client_authenticated, self.staff.user, "hostel77")

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_apply_read_only_at_a_member(self):
        """
        Applies a read only sanction at a member given by a staff user.
        """
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertFalse(response.data.get("can_write"))

    def test_apply_read_only_at_a_user_not_synchronized(self):
        """
        Applies a read only sanction at a user not synchronized.
        """
        decal = ProfileNotSyncFactory()

        response = self.client_authenticated.post(reverse("api:member:read-only", args=[decal.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), decal.user.id)

    def test_apply_temporary_read_only_at_a_member(self):
        """
        Applies a temporary read only sanction at a member given by a staff user.
        """
        data = {"ls-jrs": 1}
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertFalse(response.data.get("can_write"))
        self.assertIsNotNone(response.data.get("end_ban_write"))

    def test_apply_read_only_at_a_member_with_justification(self):
        """
        Applies a read only sanction at a member given by a staff user with a justification.
        """
        data = {"ls-text": "You are a bad boy!"}
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertFalse(response.data.get("can_write"))

    def test_apply_read_only_at_a_member_not_exist(self):
        """
        Applies a read only sanction at a member given but not present in the database.
        """
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_apply_read_only_at_a_member_with_unauthenticated_client(self):
        """
        Tries to apply a read only sanction at a member with a user isn't authenticated.
        """
        client = APIClient()
        response = client.post(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_apply_read_only_at_a_member_without_permissions(self):
        """
        Tries to apply a read only sanction at a member with a user isn't authenticated.
        """
        client_authenticated = APIClient()
        authenticate_oauth2_client(client_authenticated, self.profile.user, "hostel77")

        response = client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_read_only_at_a_member(self):
        """
        Removes a read only sanction at a member given by a staff user.
        """
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client_authenticated.delete(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertTrue(response.data.get("can_write"))

    def test_remove_temporary_read_only_at_a_member(self):
        """
        Removes a temporary read only sanction at a member given by a staff user.
        """
        data = {"ls-jrs": 1}
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client_authenticated.delete(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertTrue(response.data.get("can_write"))
        self.assertIsNone(response.data.get("end_ban_write"))

    def test_remove_read_only_at_a_member_with_justification(self):
        """
        Removes a read only sanction at a member given by a staff user with a justification.
        """
        data = {"ls-text": "You are a bad boy!"}
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client_authenticated.delete(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertTrue(response.data.get("can_write"))

    def test_remove_read_only_at_a_member_not_exist(self):
        """
        Removes a read only sanction at a member given but not present in the database.
        """
        response = self.client_authenticated.delete(reverse("api:member:read-only", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_read_only_at_a_member_with_unauthenticated_client(self):
        """
        Tries to remove a read only sanction at a member with a user isn't authenticated.
        """
        client = APIClient()
        response = client.delete(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_read_only_at_a_member_without_permissions(self):
        """
        Tries to remove a read only sanction at a member with a user isn't authenticated.
        """
        client_authenticated = APIClient()
        authenticate_oauth2_client(client_authenticated, self.profile.user, "hostel77")

        response = client_authenticated.delete(reverse("api:member:read-only", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_apply_read_only_on_self(self):
        """
        A staff user can not put LS on himself
        """
        data = {"ls-text": "I am a bad staff!"}
        response = self.client_authenticated.post(reverse("api:member:read-only", args=[self.staff.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MemberDetailBanAPITest(APITestCase):
    def setUp(self):
        self.mas = ProfileFactory()
        settings.ZDS_APP["member"]["bot_account"] = self.mas.user.username

        self.profile = ProfileFactory()
        self.staff = StaffProfileFactory()
        self.client_authenticated = APIClient()
        authenticate_oauth2_client(self.client_authenticated, self.staff.user, "hostel77")

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_apply_ban_at_a_member(self):
        """
        Applies a ban sanction at a member given by a staff user.
        """
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertFalse(response.data.get("can_read"))

    def test_apply_ban_at_a_user_not_synchronized(self):
        """
        Applies a ban sanction at a user not synchronized.
        """
        decal = ProfileNotSyncFactory()

        response = self.client_authenticated.post(reverse("api:member:ban", args=[decal.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), decal.user.id)

    def test_apply_temporary_ban_at_a_member(self):
        """
        Applies a temporary ban sanction at a member given by a staff user.
        """
        data = {"ban-jrs": 1}
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertFalse(response.data.get("can_read"))
        self.assertIsNotNone(response.data.get("end_ban_read"))

    def test_apply_ban_at_a_member_with_justification(self):
        """
        Applies a ban sanction at a member given by a staff user with a justification.
        """
        data = {"ban-text": "You are a bad boy!"}
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertFalse(response.data.get("can_read"))

    def test_apply_ban_at_a_member_not_exist(self):
        """
        Applies a ban sanction at a member given but not present in the database.
        """
        response = self.client_authenticated.post(reverse("api:member:ban", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_apply_ban_at_a_member_with_unauthenticated_client(self):
        """
        Tries to apply a ban sanction at a member with a user isn't authenticated.
        """
        client = APIClient()
        response = client.post(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_apply_ban_at_a_member_without_permissions(self):
        """
        Tries to apply a ban sanction at a member with a user isn't authenticated.
        """
        client_authenticated = APIClient()
        authenticate_oauth2_client(client_authenticated, self.profile.user, "hostel77")

        response = client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_ban_at_a_member(self):
        """
        Removes a ban sanction at a member given by a staff user.
        """
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client_authenticated.delete(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertTrue(response.data.get("can_read"))

    def test_remove_temporary_ban_at_a_member(self):
        """
        Removes a temporary ban sanction at a member given by a staff user.
        """
        data = {"ban-jrs": 1}
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client_authenticated.delete(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertTrue(response.data.get("can_read"))
        self.assertIsNone(response.data.get("end_ban_read"))

    def test_remove_ban_at_a_member_with_justification(self):
        """
        Removes a ban sanction at a member given by a staff user with a justification.
        """
        data = {"ban-text": "You are a bad boy!"}
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.profile.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client_authenticated.delete(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("username"), self.profile.user.username)
        self.assertEqual(response.data.get("email"), self.profile.user.email)
        self.assertTrue(response.data.get("can_read"))

    def test_remove_ban_at_a_member_not_exist(self):
        """
        Removes a ban sanction at a member given but not present in the database.
        """
        response = self.client_authenticated.delete(reverse("api:member:ban", args=[42]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_ban_at_a_member_with_unauthenticated_client(self):
        """
        Tries to remove a ban sanction at a member with a user isn't authenticated.
        """
        client = APIClient()
        response = client.delete(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_ban_at_a_member_without_permissions(self):
        """
        Tries to remove a ban sanction at a member with a user isn't authenticated.
        """
        client_authenticated = APIClient()
        authenticate_oauth2_client(client_authenticated, self.profile.user, "hostel77")

        response = client_authenticated.delete(reverse("api:member:ban", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_apply_ban_on_self(self):
        """
        A staff user can not put a ban on himself
        """
        data = {"ban-text": "I am a bad staff!"}
        response = self.client_authenticated.post(reverse("api:member:ban", args=[self.staff.user.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PermissionMemberAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.staff = StaffProfileFactory()

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_has_read_permission_for_anonymous_users(self):
        """
        Anonymous users have the permission to read any member.
        """
        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("read"))

    def test_has_read_permission_for_authenticated_users(self):
        """
        Authenticated users have the permission to read any member.
        """
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("read"))

    def test_has_read_permission_for_staff_users(self):
        """
        Staff users have the permission to read any member.
        """
        authenticate_oauth2_client(self.client, self.staff.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("read"))

    def test_has_not_write_permission_for_anonymous_user(self):
        """
        An anonymous user haven't write permissions.
        """
        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("write"))

    def test_has_write_permission_for_authenticated_user(self):
        """
        A user authenticated have write permissions.
        """
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("write"))

    def test_has_write_permission_for_staff(self):
        """
        A staff user have write permissions.
        """
        authenticate_oauth2_client(self.client, self.staff.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("write"))

    def test_has_not_update_permission_for_anonymous_user(self):
        """
        Only the user authenticated have update permissions.
        """
        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("update"))

    def test_has_update_permission_for_authenticated_user(self):
        """
        Only the user authenticated have update permissions.
        """
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("update"))

    def test_has_not_update_permission_for_staff(self):
        """
        Only the user authenticated have update permissions.
        """
        authenticate_oauth2_client(self.client, self.staff.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("update"))

    def test_has_not_ban_permission_for_anonymous_user(self):
        """
        Only staff have ban permission.
        """
        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("ban"))

    def test_has_not_ban_permission_for_authenticated_user(self):
        """
        Only staff have ban permission.
        """
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get("permissions").get("ban"))

    def test_has_ban_permission_for_staff(self):
        """
        Only staff have ban permission.
        """
        authenticate_oauth2_client(self.client, self.staff.user, "hostel77")

        response = self.client.get(reverse("api:member:detail", args=[self.profile.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("permissions").get("ban"))


class CacheMemberAPITest(APITestCase):
    def setUp(self):
        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()

    def test_cache_of_user_authenticated_for_member_profile(self):
        """
        Cache must be invalidated when we specify a bearer token.
        """
        profile = ProfileFactory()
        another_profile = ProfileFactory()

        authenticate_oauth2_client(self.client, profile.user, "hostel77")
        response = self.client.get(reverse("api:member:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.user.username, response.data.get("username"))

        authenticate_oauth2_client(self.client, another_profile.user, "hostel77")
        response = self.client.get(reverse("api:member:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(another_profile.user.username, response.data.get("username"))

    def test_cache_invalidated_when_new_member(self):
        """
        When we create a new member, the api cache is invalidated and returns the new member.
        """
        count = self.client.get(reverse("api:member:list")).data.get("count")

        ProfileFactory()

        response = self.client.get(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count + 1)

        second = ProfileFactory()

        response = self.client.get(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count + 2)

        second.delete()

        response = self.client.get(reverse("api:member:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count + 1)
