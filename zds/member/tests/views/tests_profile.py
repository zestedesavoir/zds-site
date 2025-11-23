from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.member.models import Profile
from zds.member.tests.factories import DevProfileFactory, ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents


@override_for_contents()
class MemberTests(TutorialTestMixin, TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory()
        settings.ZDS_APP["member"]["bot_account"] = self.mas.user.username
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
        self.category1 = ForumCategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.staff = StaffProfileFactory().user

        self.bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot.save()

    def test_list_members(self):
        """
        To test the listing of the members with and without page parameter.
        """

        # create strange member
        weird = ProfileFactory()
        weird.user.username = "ïtrema718"
        weird.user.email = "foo@\xfbgmail.com"
        weird.user.save()

        # list of members.
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)

        nb_users = len(result.context["members"])

        # Test that inactive user don't show up
        unactive_user = ProfileFactory()
        unactive_user.user.is_active = False
        unactive_user.user.save()
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context["members"]))

        # Add a Bot and check that list didn't change
        bot_profile = ProfileFactory()
        bot_profile.user.groups.add(self.bot)
        bot_profile.user.save()
        result = self.client.get(reverse("member-list"), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context["members"]))

        # list of members with page parameter.
        result = self.client.get(reverse("member-list") + "?page=1", follow=False)
        self.assertEqual(result.status_code, 200)

        # page which doesn't exist.
        result = self.client.get(reverse("member-list") + "?page=1534", follow=False)
        self.assertEqual(result.status_code, 404)

        # page parameter isn't an integer.
        result = self.client.get(reverse("member-list") + "?page=abcd", follow=False)
        self.assertEqual(result.status_code, 404)

    def test_details_member(self):
        """
        To test details of a member given.
        """
        # Test staff user profile without activity on forums first
        result = self.client.get(reverse("member-detail", args=[self.staff.username]), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertNotContains(result, "Derniers sujets créés")  # Checks that no topics are shown

        # Add a forum topic
        topic = TopicFactory(forum=self.forum11, author=self.staff)
        PostFactory(topic=topic, author=self.staff, position=1)

        # Test profile with some activity on forums
        result = self.client.get(reverse("member-detail", args=[self.staff.username]), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Derniers sujets créés")  # Checks that topics section is shown
        self.assertContains(result, topic.title)  # Checks that the topic is displayed

        # details of an unknown user.
        result = self.client.get(reverse("member-detail", args=["unknown_user"]), follow=False)
        self.assertEqual(result.status_code, 404)

    def test_redirection_when_using_old_detail_member_url(self):
        """
        To test the redirection when accessing the member profile through the old url
        """
        user = ProfileFactory().user
        result = self.client.get(reverse("member-detail-redirect", args=[user.username]), follow=False)

        self.assertEqual(result.status_code, 301)

    def test_old_detail_member_url_with_unexistant_member(self):
        """
        To test wether a 404 error is raised when the user in the old url does not exist
        """
        response = self.client.get(reverse("member-detail-redirect", args=["tartempion"]), follow=False)

        self.assertEqual(response.status_code, 404)

    def test_profile_page_of_weird_member_username(self):
        # create some user with weird username
        user_1 = ProfileFactory()
        user_2 = ProfileFactory()
        user_3 = ProfileFactory()
        user_1.user.username = "ïtrema"
        user_1.user.save()
        user_2.user.username = "&#34;a"
        user_2.user.save()
        user_3.user.username = "_`_`_`_"
        user_3.user.save()

        # profile pages of weird users.
        result = self.client.get(reverse("member-detail", args=[user_1.user.username]), follow=True)
        self.assertEqual(result.status_code, 200)
        result = self.client.get(reverse("member-detail", args=[user_2.user.username]), follow=True)
        self.assertEqual(result.status_code, 200)
        result = self.client.get(reverse("member-detail", args=[user_3.user.username]), follow=True)
        self.assertEqual(result.status_code, 200)

    def test_modify_member(self):
        user = ProfileFactory().user

        # we need staff right for update other profile, so a member who is not staff can't access to the page
        self.client.logout()
        self.client.force_login(user)

        result = self.client.get(reverse("member-settings-mini-profile", args=["xkcd"]), follow=False)
        self.assertEqual(result.status_code, 403)

        self.client.logout()
        self.client.force_login(self.staff)

        # an inexistant member return 404
        result = self.client.get(reverse("member-settings-mini-profile", args=["xkcd"]), follow=False)
        self.assertEqual(result.status_code, 404)

        # an existant member return 200
        result = self.client.get(reverse("member-settings-mini-profile", args=[self.mas.user.username]), follow=False)
        self.assertEqual(result.status_code, 200)

    def test_success_preview_biography(self):
        member = ProfileFactory()
        self.client.force_login(member.user)

        response = self.client.post(
            reverse("update-member"),
            {
                "text": "It is **my** life",
                "preview": "",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        result_string = "".join(a.decode() for a in response.streaming_content)
        self.assertIn("<strong>my</strong>", result_string, "We need the biography to be properly formatted")

    def test_members_are_contactable(self):
        """
        The PM button is displayed to logged in users, except if it's the profile
        of a banned user.
        """
        user_ban = ProfileFactory()
        user_ban.can_read = False
        user_ban.can_write = False
        user_ban.save()
        user_1 = ProfileFactory()
        user_2 = ProfileFactory()

        phrase = "Envoyer un message"

        # The PM button is hidden for anonymous users
        result = self.client.get(reverse("member-detail", args=[user_1.user.username]), follow=False)
        self.assertNotContains(result, phrase)

        # Also for anonymous users viewing banned members profiles
        result = self.client.get(reverse("member-detail", args=[user_ban.user.username]), follow=False)
        self.assertNotContains(result, phrase)

        self.client.force_login(user_2.user)

        # If an user is logged in, the PM button is shown for other normal users
        result = self.client.get(reverse("member-detail", args=[user_1.user.username]), follow=False)
        self.assertContains(result, phrase)

        # But not for banned users
        result = self.client.get(reverse("member-detail", args=[user_ban.user.username]), follow=False)
        self.assertNotContains(result, phrase)

        self.client.logout()
        self.client.force_login(user_1.user)

        # Neither for his own profile
        result = self.client.get(reverse("member-detail", args=[user_1.user.username]), follow=False)
        self.assertNotContains(result, phrase)

        self.client.logout()

    def test_github_token(self):
        user = ProfileFactory()
        dev = DevProfileFactory()

        # test that github settings are only availables for dev
        self.client.force_login(user.user)
        result = self.client.get(reverse("update-github"), follow=False)
        self.assertEqual(result.status_code, 403)
        result = self.client.post(reverse("remove-github"), follow=False)
        self.assertEqual(result.status_code, 403)
        self.client.logout()

        # now, test the form
        self.client.force_login(dev.user)
        result = self.client.get(reverse("update-github"), follow=False)
        self.assertEqual(result.status_code, 200)
        result = self.client.post(
            reverse("update-github"),
            {
                "github_token": "test",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # refresh
        dev = Profile.objects.get(pk=dev.pk)
        self.assertEqual(dev.github_token, "test")

        # test the option to remove the token
        result = self.client.post(reverse("remove-github"), follow=False)
        self.assertEqual(result.status_code, 302)

        # refresh
        dev = Profile.objects.get(pk=dev.pk)
        self.assertEqual(dev.github_token, "")

    def test_markdown_help_settings(self):
        user = ProfileFactory().user

        # login and check that the Markdown help is displayed
        self.client.force_login(user)
        result = self.client.get(reverse("pages-index"), follow=False)
        self.assertContains(result, 'data-show-markdown-help="true"')

        # disable Markdown help
        user.profile.show_markdown_help = False
        user.profile.save()
        result = self.client.get(reverse("pages-index"), follow=False)
        self.assertContains(result, 'data-show-markdown-help="false"')
