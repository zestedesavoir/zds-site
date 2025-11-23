from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.gallery.models import UserGallery
from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory


@override_for_contents()
class RemoveAuthor(TutorialTestMixin, TestCase):
    def setUp(self):
        self.bot_group = Group(name=settings.ZDS_APP["member"]["bot_group"])
        self.bot_group.save()

        self.overridden_zds_app["member"]["bot_account"] = ProfileFactory().user.username

        self.author = ProfileFactory().user
        self.other_author = ProfileFactory().user

        self.external = ProfileFactory().user
        self.external.username = self.overridden_zds_app["member"]["external_account"]
        self.external.save()
        self.external.groups.add(self.bot_group)

        self.tuto = PublishableContentFactory(type="TUTORIAL", author_list=[self.author, self.other_author])

        self.client.force_login(self.author)

    @patch("zds.tutorialv2.signals.authors_management")
    def test_nominal(self, authors_management):
        """Removing a member effectively being an author."""
        result = self.client.post(
            reverse("content:remove-author", args=[self.tuto.pk]),
            {"username": self.other_author.username},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 1)
        self.assertEqual(authors_management.send.call_count, 1)
        self.assertEqual(authors_management.send.call_args[1]["action"], "remove")

        self.assertIsNone(UserGallery.objects.filter(gallery=self.tuto.gallery, user=self.other_author).first())

    @patch("zds.tutorialv2.signals.authors_management")
    def test_not_existing(self, authors_management):
        """Attempting to remove a user who is not author shall do nothing."""
        result = self.client.post(
            reverse("content:remove-author", args=[self.tuto.pk]), {"username": "unknown"}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 2)
        self.assertEqual(authors_management.send.call_count, 0)

    @patch("zds.tutorialv2.signals.authors_management")
    def test_last_remaining(self, authors_management):
        """Attempting to remove the last author shall lead to no change."""
        self.tuto.authors.remove(self.other_author)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 1)

        result = self.client.post(
            reverse("content:remove-author", args=[self.tuto.pk]), {"username": self.author.username}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 1)
        self.assertEqual(authors_management.send.call_count, 0)

    @patch("zds.tutorialv2.signals.authors_management")
    def test_self(self, authors_management):
        """An author removes themselves."""
        result = self.client.post(
            reverse("content:remove-author", args=[self.tuto.pk]), {"username": self.author.username}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.authors.count(), 1)
        self.assertFalse(tuto.authors.filter(pk=self.author.pk).exists())
        self.assertEqual(authors_management.send.call_count, 1)
        self.assertEqual(authors_management.send.call_args[1]["action"], "remove")

    @patch("zds.tutorialv2.signals.authors_management")
    def test_bot(self, authors_management):
        """
        Bots can be removed from the authors.
        Check a non-regression on a bug where exceptions were raised when removing "Auteur externe" from the authors.
        """
        self.tuto.authors.add(self.external)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 3)

        result = self.client.post(
            reverse("content:remove-author", args=[self.tuto.pk]), {"username": self.external.username}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.authors.count(), 2)
        self.assertFalse(tuto.authors.filter(pk=self.external.pk).exists())
        self.assertEqual(authors_management.send.call_count, 1)
        self.assertEqual(authors_management.send.call_args[1]["action"], "remove")
