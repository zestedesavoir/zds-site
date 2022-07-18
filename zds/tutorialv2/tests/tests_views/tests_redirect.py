from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory


class RedirectOldContentOfAuthorTest(TestCase):
    def test_redirect(self):
        user = ProfileFactory().user

        response = self.client.get(reverse("content:legacy-find-tutorial", args=[user.pk]))
        self.assertRedirects(response, reverse("tutorial:find-tutorial", args=[user]), status_code=301)

        response = self.client.get(reverse("content:legacy-find-article", args=[user.pk]))
        self.assertRedirects(response, reverse("article:find-article", args=[user]), status_code=301)

        response = self.client.get(reverse("content:legacy-find-opinion", args=[user.pk]))
        self.assertRedirects(response, reverse("opinion:find-opinion", args=[user]), status_code=301)

        # The user with pk=3954 doesn't exist (the view in the redirection
        # triggers the 404, so we need to follow the response):
        response = self.client.get(reverse("content:legacy-find-tutorial", args=[3954]), follow=True)
        self.assertEqual(response.status_code, 404)
