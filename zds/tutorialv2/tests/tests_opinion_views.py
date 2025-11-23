import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.tests.factories import TagFactory
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.notification.models import Notification
from zds.tutorialv2.models.database import PickListOperation, PublicationEvent, PublishableContent, PublishedContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ExtractFactory, PublishableContentFactory, PublishedContentFactory
from zds.utils.models import Alert
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


@override_for_contents()
class PublishedContentTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app["member"]["bot_account"] = ProfileFactory().user.username
        self.bot_group = Group()
        self.bot_group.name = settings.ZDS_APP["member"]["bot_group"]
        self.bot_group.save()
        self.licence = LicenceFactory()
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.anonymous.groups.add(self.bot_group)
        self.anonymous.save()
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
        self.external.groups.add(self.bot_group)
        self.external.save()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

    @patch("zds.tutorialv2.signals.opinions_management")
    def test_opinion_publication_author(self, opinions_management):
        """
        Test the publication of PublishableContent where type is OPINION (with author).
        """

        text_publication = "Aussi tôt dit, aussi tôt fait !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # By visiting the published content, the author marks the publication notification as read:
        self.assertEqual(Notification.objects.get_unread_notifications_of(self.user_author).count(), 1)
        self.client.get(result.url)
        self.assertEqual(Notification.objects.get_unread_notifications_of(self.user_author).count(), 0)

    @patch("zds.tutorialv2.signals.opinions_management")
    def test_publish_content_change_title_before_watchdog(self, opinions_management):
        """
        Test we can publish a content, change its title and publish it again
        right away, before the publication watchdog processed the first
        publication.
        """
        previous_extra_content_generation_policy = self.overridden_zds_app["content"]["extra_content_generation_policy"]
        self.overridden_zds_app["content"]["extra_content_generation_policy"] = "WATCHDOG"

        # Create a content:
        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()

        # Publish it a first time:
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": "Blabla", "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # Change the title:
        result = self.client.post(
            reverse("content:edit-title", args=[opinion.pk]),
            {"title": f"{opinion.title} (modified)"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishedContent.objects.count(), 1)
        self.assertEqual(opinions_management.send.call_count, 1)
        self.assertEqual(opinions_management.send.call_args[1]["action"], "publish")

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # and publish it a second time now it has a new title:
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": "Blabla", "source": "", "version": opinion.sha_draft},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # There are two PublishedContent: one with the old title and the old slug
        # redirecting to the current version of the content with the new title:
        self.assertEqual(PublishedContent.objects.count(), 2)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        opinion_draft = opinion.load_version()
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        requested_events = PublicationEvent.objects.filter(state_of_processing="REQUESTED")
        self.assertEqual(requested_events.count(), 4)

        # TODO (Arnaud-D): This must be fixed as it creates coupling between tests.
        #  Other tests check the presence of exports and fail if this one is not executed successfully before.
        call_command("publication_watchdog", "--once")

        requested_events = PublicationEvent.objects.filter(state_of_processing="REQUESTED")
        self.assertEqual(requested_events.count(), 0)

        self.overridden_zds_app["content"]["extra_content_generation_policy"] = previous_extra_content_generation_policy

    def test_accessible_ui_for_author(self):
        opinion = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        subcategory = SubCategoryFactory()
        opinion.subcategory.add(subcategory)
        opinion.save()
        self.client.force_login(self.user_author)
        resp = self.client.get(reverse("opinion:view", kwargs={"pk": opinion.pk, "slug": opinion.slug}))
        self.assertContains(resp, "Voir la page brouillon", msg_prefix="Author must access their draft directly")
        self.assertNotContains(resp, "{}?subcategory=".format(reverse("publication:list")))
        self.assertContains(resp, "{}?category=".format(reverse("opinion:list")))

    def test_opinion_publication_staff(self):
        """
        Test the publication of PublishableContent where type is OPINION (with staff).
        """

        text_publication = "Aussi tôt dit, aussi tôt fait !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

    @patch("zds.tutorialv2.signals.opinions_management")
    def test_opinion_publication_guest(self, opinions_management):
        """
        Test the publication of PublishableContent where type is OPINION (with guest => 403).
        """

        text_publication = "Aussi tôt dit, aussi tôt fait !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_guest)

        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)
        self.assertEqual(opinions_management.send.call_count, 0)

        self.assertEqual(PublishedContent.objects.count(), 0)

    @patch("zds.tutorialv2.signals.opinions_management")
    def test_opinion_unpublication(self, opinions_management):
        """
        Test the unpublication of PublishableContent where type is OPINION (with author).
        """

        text_publication = "Aussi tôt dit, aussi tôt fait !"
        text_unpublication = "Au revoir !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        # author

        self.client.force_login(self.user_author)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)
        self.assertEqual(opinions_management.send.call_count, 1)
        self.assertEqual(opinions_management.send.call_args[1]["action"], "publish")

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # unpublish
        result = self.client.post(
            reverse("validation:unpublish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_unpublication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 0)
        self.assertEqual(opinions_management.send.call_count, 2)
        self.assertEqual(opinions_management.send.call_args[1]["action"], "unpublish")

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.public_version)

        # staff

        self.client.force_login(self.user_staff)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # unpublish
        result = self.client.post(
            reverse("validation:unpublish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_unpublication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 0)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.public_version)

        # guest => 403

        self.client.force_login(self.user_author)

        # publish with author
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        self.client.force_login(self.user_guest)

        # unpublish
        result = self.client.post(
            reverse("validation:unpublish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_unpublication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        self.assertEqual(PublishedContent.objects.count(), 1)

        # unregister author and unpublish
        self.client.force_login(self.user_author)
        result = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
        self.assertEqual(result.status_code, 302)

        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:unpublish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_unpublication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 0)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.public_version)

    def test_opinion_validation(self):
        """
        Test the validation of PublishableContent where type is OPINION.
        """

        text_publication = "Aussi tôt dit, aussi tôt fait !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # valid with author => 403
        opinion = PublishableContent.objects.get(pk=opinion.pk)
        opinion_draft = opinion.load_version()

        result = self.client.post(
            reverse("validation:pick-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.sha_picked)
        self.assertIsNone(opinion.picked_date)

        self.client.force_login(self.user_staff)

        # valid with staff
        result = self.client.post(
            reverse("validation:pick-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertEqual(opinion.sha_picked, opinion_draft.current_version)
        self.assertIsNotNone(opinion.picked_date)

        # invalid with author => 403
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:unpick-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": "Parce que je veux", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertEqual(opinion.sha_picked, opinion_draft.current_version)

        # invalid with staff
        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:unpick-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": "Parce que je peux !", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.sha_picked)

        # double invalidation wont work
        result = self.client.post(
            reverse("validation:unpick-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": "Parce que je peux toujours ...", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

    def test_ignore_opinion(self):
        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # ignore with author => 403
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "NO_PICK",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        # now, login as staff
        self.client.force_login(self.user_staff)

        # check that the opinion is displayed
        result = self.client.get(reverse("validation:list-opinion"))
        self.assertContains(result, opinion.title)

        # ignore the opinion
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "NO_PICK",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # check that the opinion is not displayed
        result = self.client.get(reverse("validation:list-opinion"))
        self.assertNotContains(result, opinion.title)

        # publish the opinion again
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # check that the opinion is displayed
        result = self.client.get(reverse("validation:list-opinion"))
        self.assertContains(result, opinion.title)

        # reject it
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "REJECT",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # publish again
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # check that the opinion is not displayed
        result = self.client.get(reverse("validation:list-opinion"))
        self.assertNotContains(result, opinion.title)

    def test_permanently_unpublish_opinion(self):
        for unregister_author in [False, True]:
            with self.subTest(unregister_author):
                opinion = PublishableContentFactory(type="OPINION")

                opinion.authors.add(self.user_author)
                UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
                opinion.licence = self.licence
                opinion.save()

                opinion_draft = opinion.load_version()
                ExtractFactory(container=opinion_draft, db_object=opinion)
                ExtractFactory(container=opinion_draft, db_object=opinion)

                self.client.force_login(self.user_author)

                # publish
                result = self.client.post(
                    reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
                    {"source": "", "version": opinion_draft.current_version},
                    follow=False,
                )
                self.assertEqual(result.status_code, 302)

                if unregister_author:
                    result = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
                    self.assertEqual(result.status_code, 302)

                # login as staff
                self.client.force_login(self.user_staff)

                # unpublish opinion
                result = self.client.post(
                    reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
                    {
                        "operation": "REMOVE_PUB",
                    },
                    follow=False,
                )
                self.assertEqual(result.status_code, 200)

                # refresh
                opinion = PublishableContent.objects.get(pk=opinion.pk)

                # check that the opinion is not published
                self.assertFalse(opinion.in_public())

                # check that it's impossible to publish the opinion again
                result = self.client.get(opinion.get_absolute_url())
                self.assertContains(result, _("Billet modéré"))  # front

                result = self.client.post(
                    reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
                    {"source": "", "version": opinion_draft.current_version},
                    follow=False,
                )
                self.assertEqual(result.status_code, 403)  # back

    def test_defenitely_unpublish_alerted_opinion(self):
        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login as staff
        self.client.force_login(self.user_staff)
        alerter = ProfileFactory().user
        Alert.objects.create(
            author=alerter,
            scope="CONTENT",
            content=opinion,
            pubdate=datetime.datetime.now(),
            text="J'ai un probleme avec cette opinion : c'est pas la mienne.",
        )
        # unpublish opinion
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "REMOVE_PUB",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # refresh
        opinion = PublishableContent.objects.get(pk=opinion.pk)

        # check that the opinion is not published
        self.assertFalse(opinion.in_public())

        # check that it's impossible to publish the opinion again
        result = self.client.get(opinion.get_absolute_url())
        self.assertContains(result, _("Billet modéré"))  # front

        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)  # back
        self.assertTrue(Alert.objects.filter(content=opinion).last().solved)
        # check alert page is still accessible and our alert is well displayed
        resp = self.client.get(reverse("pages-alerts"))
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.context["alerts"]))
        self.assertEqual(1, len(resp.context["solved"]))

    def test_cancel_pick_operation(self):
        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login as staff
        self.client.force_login(self.user_staff)

        # PICK
        result = self.client.post(
            reverse("validation:pick-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # cancel the operation
        operation = PickListOperation.objects.latest("operation_date")
        result = self.client.post(
            reverse("validation:revoke-ignore-opinion", kwargs={"pk": operation.pk}), follow=False
        )
        self.assertEqual(result.status_code, 200)

        # refresh
        operation = PickListOperation.objects.get(pk=operation.pk)
        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertFalse(operation.is_effective)
        self.assertEqual(self.user_staff, operation.canceler_user)
        self.assertIsNone(opinion.sha_picked)

        # NO_PICK
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "NO_PICK",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # cancel the operation
        operation = PickListOperation.objects.latest("operation_date")
        result = self.client.post(
            reverse("validation:revoke-ignore-opinion", kwargs={"pk": operation.pk}), follow=False
        )
        self.assertEqual(result.status_code, 200)

        # check that the opinion is displayed on validation page
        result = self.client.get(reverse("validation:list-opinion"))
        self.assertContains(result, opinion.title)

        # REMOVE_PUB
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "REMOVE_PUB",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # cancel the operation
        operation = PickListOperation.objects.latest("operation_date")
        result = self.client.post(
            reverse("validation:revoke-ignore-opinion", kwargs={"pk": operation.pk}), follow=False
        )
        self.assertEqual(result.status_code, 200)

        # check that the opinion can be published again
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

    def test_opinion_conversion(self):
        """
        Test the conversion of PublishableContent with type=OPINION
        to PublishableContent with type=ARTICLE
        """

        text_publication = "Aussi tôt dit, aussi tôt fait !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        # publish
        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # valid with author => 403
        result = self.client.post(
            reverse("validation:promote-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        self.client.force_login(self.user_staff)

        # valid with staff
        result = self.client.post(
            reverse("validation:promote-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

    def test_opinion_alert(self):
        """Test content alert"""

        text_publication = "Aussi tôt dit, aussi tôt fait !"

        opinion = PublishableContentFactory(type="OPINION")

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:publish-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {"text": text_publication, "source": "", "version": opinion_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # Alert content
        random_user = ProfileFactory().user

        self.client.force_login(random_user)

        result = self.client.post(
            reverse("content:alert-content", kwargs={"pk": opinion.pk}), {"signal_text": "Yeurk !"}, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(Alert.objects.filter(author__pk=random_user.pk, content__pk=opinion.pk).first())

        alert = Alert.objects.filter(author__pk=random_user.pk, content__pk=opinion.pk).first()
        self.assertFalse(alert.solved)

        result = self.client.post(
            reverse("content:resolve-content", kwargs={"pk": opinion.pk}),
            {"alert_pk": alert.pk, "text": "Je peux ?"},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)  # solving the alert by yourself wont work

        alert = Alert.objects.get(pk=alert.pk)
        self.assertFalse(alert.solved)

        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("content:resolve-content", kwargs={"pk": opinion.pk}),
            {"alert_pk": alert.pk, "text": "Anéfé!"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        alert = Alert.objects.get(pk=alert.pk)
        self.assertTrue(alert.solved)

    def test_tag_list_is_slug(self):
        tag = TagFactory(title="Test Slug")
        result = self.client.get(reverse("opinion:list"), {"tag": tag.slug})
        self.assertEqual(result.status_code, 200)
