from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.gallery.models import GALLERY_WRITE, UserGallery
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, UserFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory


@override_for_contents()
class AddAuthorTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.bot_group = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot_group.save()

        self.overridden_zds_app["member"]["bot_account"] = ProfileFactory().user.username

        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.external = UserFactory(username=self.overridden_zds_app["member"]["external_account"])
        self.external.groups.add(self.bot_group)
        self.external.save()

        self.tuto = PublishableContentFactory(type="TUTORIAL", author_list=[self.user_author])
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode="W")

        self.client.force_login(self.user_author)

    @patch("zds.tutorialv2.signals.authors_management")
    def test_nominal(self, authors_management):
        result = self.client.post(
            reverse("content:add-author", args=[self.tuto.pk]), {"username": self.user_guest.username}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 2)
        gallery = UserGallery.objects.filter(gallery=self.tuto.gallery, user=self.user_guest).first()
        self.assertIsNotNone(gallery)
        self.assertEqual(GALLERY_WRITE, gallery.mode)
        self.assertEqual(authors_management.send.call_count, 1)
        self.assertEqual(authors_management.send.call_args[1]["action"], "add")

    @patch("zds.tutorialv2.signals.authors_management")
    def test_not_existing_user(self, authors_management):
        result = self.client.post(
            reverse("content:add-author", args=[self.tuto.pk]), {"username": "unknown"}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 1)
        self.assertEqual(authors_management.send.call_count, 0)

    @patch("zds.tutorialv2.signals.authors_management")
    def test_bot(self, authors_management):
        result = self.client.post(
            reverse("content:add-author", args=[self.tuto.pk]), {"username": self.external.username}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 1)
        self.assertEqual(authors_management.send.call_count, 0)
