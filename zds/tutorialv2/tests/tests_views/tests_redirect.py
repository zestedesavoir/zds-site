from django.test import TestCase

from zds.member.tests.factories import ProfileFactory


class RedirectOldContentOfAuthorTest(TestCase):
    def test_redirect(self):
        user = ProfileFactory().user

        response = self.client.get(f"/contenus/tutoriels/{user.pk}", follow=True)
        self.assertRedirects(response, f"/tutoriels/voir/{user}/", status_code=301)

        response = self.client.get(f"/contenus/articles/{user.pk}", follow=True)
        self.assertRedirects(response, f"/articles/voir/{user}/", status_code=301)

        response = self.client.get(f"/contenus/tribunes/{user.pk}", follow=True)
        self.assertRedirects(response, f"/billets/voir/{user}/", status_code=301)

        response = self.client.get(f"/contenus/foo/{user.pk}", follow=True)
        self.assertEqual(response.status_code, 404)

        # The user with pk=3954 doesn't exist:
        response = self.client.get("/contenus/tutoriels/3954", follow=True)
        self.assertEqual(response.status_code, 404)
