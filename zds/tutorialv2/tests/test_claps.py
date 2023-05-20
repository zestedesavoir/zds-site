from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory, ClapFactory


@override_for_contents()
class ClapsTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.user_author = ProfileFactory().user
        self.tuto = PublishableContentFactory(title="Mon super tuto", type="TUTORIAL", author_list=[self.user_author])

    def test_can_add_claps(self):
        user1 = ProfileFactory().user
        self.client.force_login(user1)
        try:
            result = self.client.post(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_cannot_add_claps_invalid_publication(self):
        user1 = ProfileFactory().user
        self.client.force_login(user1)
        try:
            result = self.client.post(reverse("api:content:claps", args=[10000]), follow=False)
        except Exception:
            self.fail("Exception")

        print(result.data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(None, result.data.get("publication"))

    def test_cannot_add_claps_not_logged_in(self):
        self.client.logout()
        try:
            result = self.client.post(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")
        print(result.data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(None, result.data.get("user"))

    def test_can_delete_clap(self):
        user1 = ProfileFactory().user
        ClapFactory(publication=self.tuto, user=user1)
        self.client.force_login(user1)
        try:
            result = self.client.delete(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")

        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)

    def test_can_create_clap_after_deletion(self):
        user1 = ProfileFactory().user
        ClapFactory(publication=self.tuto, user=user1)
        self.client.force_login(user1)
        try:
            result = self.client.delete(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")
        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)

        try:
            result = self.client.post(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_can_get_clap_for_user(self):
        user1 = ProfileFactory().user
        ClapFactory(publication=self.tuto, user=user1)
        self.client.force_login(user1)
        try:
            result = self.client.get(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")
        self.assertEqual(result.status_code, status.HTTP_302_FOUND)
        self.assertEqual(user1.id, result.data.get("user"))
        self.assertEqual(self.tuto.id, result.data.get("publication"))

    def test_get_user_has_not_clapped(self):
        user1 = ProfileFactory().user
        self.client.force_login(user1)
        try:
            result = self.client.get(reverse("api:content:claps", args=[self.tuto.id]), follow=False)
        except Exception:
            self.fail("Exception")
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_get_claps_for_publication(self):
        user1 = ProfileFactory().user
        user2 = ProfileFactory().user
        tuto = self.create_published_tuto(user1)
        ClapFactory(publication=tuto, user=user1)
        ClapFactory(publication=tuto, user=user2)
        self.client.force_login(user1)
        try:
            result = self.client.get(reverse("tutorial:view", args=[tuto.id, tuto.slug]), follow=False)
        except Exception:
            self.fail("Exception")

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.context_data.get("nb_claps"), 2)

    def create_published_tuto(self, user1):
        tuto = PublishableContentFactory(title="Mon autre super tuto", type="TUTORIAL", author_list=[user1])

        tuto_draft = tuto.load_version()

        # then, publish it !
        version = tuto_draft.current_version
        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = version
        tuto.sha_draft = version
        tuto.public_version = published
        tuto.save()
        return tuto
