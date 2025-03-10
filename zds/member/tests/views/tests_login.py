from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.member.forms import LoginForm
from zds.member.models import Ban, Profile
from zds.member.tests.factories import NonAsciiProfileFactory, ProfileFactory, StaffProfileFactory


class LoginTests(TestCase):
    def setUp(self):
        self.profile = ProfileFactory()  # associated user is activated by default
        self.correct_username = self.profile.user.username
        self.wrong_username = "I_do_not_exist"
        self.correct_password = "hostel77"
        self.wrong_password = "XXXXX"
        self.login_url = reverse("member-login")
        self.test_ip = "192.168.0.110"  # must be different from the one set by the factory to test actual change
        self.assertNotEqual(self.test_ip, ProfileFactory.last_ip_address)
        settings.SESSION_COOKIE_AGE = 1337

        self.staff_profile = StaffProfileFactory()
        self.banned_profile = ProfileFactory()
        self.banned_profile.end_ban_read = None
        self.banned_profile.can_read = False
        self.banned_profile.save()
        self.ban = Ban.objects.create(
            user=self.banned_profile.user,
            moderator=self.staff_profile.user,
            type="Bannissement illimité",
            note="Test message",
            pubdate=datetime.now(),
        )
        self.ban.save()

    def test_form_action_redirect(self):
        """The form shall have the 'next' parameter in the action url of the form."""
        next_fragment = "?next=" + reverse("member-detail", args=[self.correct_username])
        full_url = self.login_url + next_fragment
        result = self.client.get(full_url, follow=False)
        self.assertContains(result, f'action="{full_url}"')

    def test_nominal_and_remember_me(self):
        """
        Nominal case: existing username, correct password, activated user, 'remember me' checked.
        Expected: successful login, redirect to homepage, session expiration age set.
        """
        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
            REMOTE_ADDR=self.test_ip,
        )

        self.assertRedirects(result, reverse("homepage"))

        # Check cookie setting
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

        # Check IP recording
        profile = Profile.objects.get(user=self.profile.user)
        self.assertEqual(profile.last_ip_address, self.test_ip)

    def test_nominal_and_do_not_remember_me(self):
        """
        Nominal case: existing username, correct password, activated user, 'remember me' not checked.
        Expected: successful login, redirect to homepage, session expiration at browser closing.
        """
        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
            },
            follow=False,
        )

        self.assertRedirects(result, reverse("homepage"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_nonascii(self):
        """
        Edge case: similar to nominal, but with non-ascii username and redirect to profile.
        Expected: successful login and redirect to profile.
        """
        user = NonAsciiProfileFactory()
        result = self.client.post(
            self.login_url + "?next=" + reverse("member-detail", args=[user.user.username]),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

    def test_empty_username_or_password(self):
        """
        Error case: bad username, password not relevant.
        Expected: cannot log in, errors associated to empty username and password.
        """
        result = self.client.post(
            self.login_url,
            {
                "username": "",
                "password": "",
                "remember": "remember",
            },
            follow=False,
        )
        self.assertContains(result, escape("Ce champ est obligatoire"), count=2)

    def test_bad_username(self):
        """
        Error case: bad username, password not relevant.
        Expected: cannot log in, error associated to bad username.
        """
        result = self.client.post(
            self.login_url,
            {
                "username": self.wrong_username,
                "password": self.wrong_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertContains(result, escape(LoginForm.error_messages["invalid_login"]))

    def test_inactive_account(self):
        """
        Error case: correct username, but inactive account.
        Expected: cannot log in error associated to inactive account.
        """
        self.profile.user.is_active = False
        self.profile.user.save()

        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertContains(result, escape(LoginForm.error_messages["inactive"][:20]))

    def test_correct_username_bad_password(self):
        """
        Error case: existing username, activated account, but wrong password.
        Expected: cannot log in, error associated to wrong password.
        """
        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.wrong_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertContains(result, escape(LoginForm.error_messages["invalid_login"]))

    def test_banned_user(self):
        """
        Error case: correct username, activated user, correct password, but banned user.
        Expected: cannot log in, error associated with the ban.
        """

        result = self.client.post(
            self.login_url,
            {
                "username": self.banned_profile.user.username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertContains(result, escape(LoginForm.error_messages["banned"].format(self.ban.note)))

    def test_previously_temp_banned_user(self):
        """
        Nominal case: correct username, activated user, correct password, previously temp banned user.
        Expected: successful login, redirect to homepage.
        """

        # Equivalent to a previously temporary banned user
        self.profile.can_read = False
        self.profile.end_ban_read = datetime.now() - timedelta(days=30)
        self.profile.save()

        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
            },
            follow=True,
        )

        self.assertRedirects(result, reverse("homepage"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_redirection_good_target(self):
        """Nominal case: redirection to an existing page with the parameter 'next'."""
        result = self.client.post(
            self.login_url + "?next=" + reverse("gallery:list"),
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertRedirects(result, reverse("gallery:list"))

    def test_redirection_bad_target(self):
        """Case failing gracefully: redirection to homepage when 'next' points to a non-existing page."""
        result = self.client.post(
            self.login_url + "?next=/this_does_not_exist",
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertRedirects(result, reverse("homepage"))

    def test_redirection_loop_avoidance(self):
        """
        Case failing gracefully: redirection to homepage when 'next' risks creating a redirection loop.
        """
        result = self.client.post(
            self.login_url + "?next=" + self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertRedirects(result, reverse("homepage"))
