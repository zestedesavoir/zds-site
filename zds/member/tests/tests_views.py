from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory


class UpdateMemberViewTest(TestCase):
    def setUp(self):
        self.profile = ProfileFactory()

    def test_full_form(self):
        self.client.force_login(self.profile.user)

        new_biography = "Biography"
        new_site = "https://perdu.com"
        new_avatar_url = "https://site.foo/img.png"
        new_sign = "My signature"

        response = self.client.post(
            reverse("update-member"),
            {"biography": new_biography, "site": new_site, "avatar_url": new_avatar_url, "sign": new_sign},
        )
        self.assertEqual(302, response.status_code)

        self.profile.refresh_from_db()

        self.assertEqual(self.profile.biography, new_biography)
        self.assertEqual(self.profile.site, new_site)
        self.assertEqual(self.profile.avatar_url, new_avatar_url)
        self.assertEqual(self.profile.sign, new_sign)

    def test_blank_form(self):
        self.client.force_login(self.profile.user)

        self.profile.biography = "Biography"
        self.profile.site = "https://perdu.com"
        self.profile.avatar_url = "https://site.foo/img.png"
        self.profile.sign = "My signature"
        self.profile.save()

        response = self.client.post(
            reverse("update-member"), {"biography": "", "site": "", "avatar_url": "", "sign": ""}
        )
        self.assertEqual(302, response.status_code)

        self.profile.refresh_from_db()

        self.assertEqual(self.profile.biography, "")
        self.assertEqual(self.profile.site, "")
        self.assertEqual(self.profile.avatar_url, "")
        self.assertEqual(self.profile.sign, "")

    def test_empty_form(self):
        self.client.force_login(self.profile.user)

        initial_biography = "Biography"
        initial_site = "https://perdu.com"
        initial_avatar_url = "https://site.foo/img.png"
        initial_sign = "My signature"

        self.profile.biography = initial_biography
        self.profile.site = initial_site
        self.profile.avatar_url = initial_avatar_url
        self.profile.sign = initial_sign
        self.profile.save()

        response = self.client.post(reverse("update-member"), {})
        self.assertEqual(302, response.status_code)

        self.profile.refresh_from_db()

        self.assertEqual(self.profile.biography, initial_biography)
        self.assertEqual(self.profile.site, initial_site)
        self.assertEqual(self.profile.avatar_url, initial_avatar_url)
        self.assertEqual(self.profile.sign, initial_sign)


class SendValidationEmailViewTest(TestCase):
    def test_get(self):
        response = self.client.get(reverse("send-validation-email"))
        self.assertEqual(200, response.status_code)

    def test_post_invalid_user(self):
        response = self.client.post(reverse("send-validation-email"), {"username": "unknown"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["form"].errors))

        response = self.client.post(reverse("send-validation-email"), {"email": "un@known"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["form"].errors))
