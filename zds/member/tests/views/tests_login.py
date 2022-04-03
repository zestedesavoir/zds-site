from django.urls import reverse
from django.test import TestCase
from django.utils.html import escape

from zds.member.forms import LoginForm
from zds.member.tests.factories import ProfileFactory, NonAsciiProfileFactory

# TODO: test correct update of IP
# TODO: test session expiration with/without "remember me"


class LoginTests(TestCase):
    def setUp(self):
        self.profile = ProfileFactory()  # associated user is activated by default
        self.correct_username = self.profile.user.username
        self.wrong_username = "I_do_not_exist"
        self.correct_password = "hostel77"
        self.wrong_password = "XXXXX"
        self.login_url = reverse("member-login")

    def test_nominal(self):
        """
        Nominal case: existing username, correct password, activated user.
        Expected: successful login and redirect to homepage.
        """
        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertRedirects(result, reverse("homepage"))

    def test_nonascii(self):
        """
        Edge case: similar to nominal, but with non-ascii username and redirect to profile.
        Expected: successful login and redirect to profile.
        """
        user = NonAsciiProfileFactory()
        result = self.client.get(
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

        # Equivalent to a banned user
        self.profile.can_read = False
        self.profile.save()

        result = self.client.post(
            self.login_url,
            {
                "username": self.correct_username,
                "password": self.correct_password,
                "remember": "remember",
            },
            follow=False,
        )
        self.assertContains(result, escape(LoginForm.error_messages["banned"]))

    def test_redirection_good_target(self):
        """Nominal case: redirection to an existing page with the parameter 'next'."""
        result = self.client.post(
            self.login_url + "?next=" + reverse("gallery-list"),
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
