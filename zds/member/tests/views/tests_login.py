from django.urls import reverse
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory, NonAsciiProfileFactory


class MemberTests(TestCase):
    def test_login(self):
        """
        To test user login.
        """
        user = ProfileFactory()

        # login a user. Good password then redirection to the homepage.
        result = self.client.post(
            reverse("member-login"),
            {"username": user.user.username, "password": "hostel77", "remember": "remember"},
            follow=False,
        )
        self.assertRedirects(result, reverse("homepage"))

        # login failed with bad password then no redirection
        # (status_code equals 200 and not 302).
        result = self.client.post(
            reverse("member-login"),
            {"username": user.user.username, "password": "hostel", "remember": "remember"},
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        self.assertContains(
            result,
            _(
                "Le mot de passe saisi est incorrect. "
                "Cliquez sur le lien « Mot de passe oublié ? » "
                "si vous ne vous en souvenez plus."
            ),
        )

        # login failed with bad username then no redirection
        # (status_code equals 200 and not 302).
        result = self.client.post(
            reverse("member-login"), {"username": "clem", "password": "hostel77", "remember": "remember"}, follow=False
        )
        self.assertEqual(result.status_code, 200)
        self.assertContains(
            result,
            _("Ce nom d’utilisateur est inconnu. " "Si vous ne possédez pas de compte, " "vous pouvez vous inscrire."),
        )

        # login a user. Good password and next parameter then
        # redirection to the "next" page.
        result = self.client.post(
            reverse("member-login") + "?next=" + reverse("gallery:list"),
            {"username": user.user.username, "password": "hostel77", "remember": "remember"},
            follow=False,
        )
        self.assertRedirects(result, reverse("gallery:list"))

        # check the user is redirected to the home page if
        # the "next" parameter points to a non-existing page.
        result = self.client.post(
            reverse("member-login") + "?next=/foobar",
            {"username": user.user.username, "password": "hostel77", "remember": "remember"},
            follow=False,
        )
        self.assertRedirects(result, reverse("homepage"))

        # check if the login form will redirect if there is
        # a next parameter.
        self.client.logout()
        result = self.client.get(reverse("member-login") + "?next=" + reverse("gallery:list"))
        self.assertContains(result, reverse("member-login") + "?next=" + reverse("gallery:list"), count=1)

    def test_nonascii(self):
        user = NonAsciiProfileFactory()
        result = self.client.get(
            reverse("member-login") + "?next=" + reverse("member-detail", args=[user.user.username]), follow=False
        )
        self.assertEqual(result.status_code, 200)
