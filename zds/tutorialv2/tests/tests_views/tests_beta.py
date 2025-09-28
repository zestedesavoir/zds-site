from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Post, Topic, TopicRead
from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, UserFactory
from zds.mp.models import PrivateTopic
from zds.notification.models import TopicAnswerSubscription
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ExtractFactory,
    HelpWritingFactory,
    PublishableContentFactory,
)
from zds.utils.models import Tag


@override_for_contents()
class BetaTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.mas = ProfileFactory().user
        self.overridden_zds_app["member"]["bot_account"] = self.mas.username

        bot_group = Group(name=self.overridden_zds_app["member"]["bot_group"])
        bot_group.save()

        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user

        self.external = UserFactory(username=self.overridden_zds_app["member"]["external_account"], password="anything")
        self.external.groups.add(bot_group)

        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode="W")
        self.tuto.save()

        self.beta_forum = ForumFactory(
            pk=self.overridden_zds_app["forum"]["beta_forum_id"],
            category=ForumCategoryFactory(position=1),
            position_in_category=1,
        )  # ensure that the forum, for the beta versions, is created

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

    @patch("zds.tutorialv2.signals.beta_management")
    def test_beta_workflow(self, beta_management):
        """Test beta workflow (access and update)"""

        # login with guest and test the non-access
        self.client.force_login(self.user_guest)
        result = self.client.get(reverse("content:view", args=[self.tuto.pk, self.tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 403)  # (get 403 since he is not part of the authors)

        # login with author
        self.client.force_login(self.user_author)
        sometag = Tag(title="randomizeit")
        sometag.save()
        self.tuto.tags.add(sometag)
        # create second author and add to tuto
        second_author = ProfileFactory().user
        self.tuto.authors.add(second_author)
        self.tuto.save()

        # activ beta:
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        current_sha_beta = tuto.sha_draft
        result = self.client.post(
            reverse("content:set-beta", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"version": current_sha_beta},
            follow=False,
        )
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(result.status_code, 302)

        # check if there is a pm corresponding to the tutorial in beta
        self.assertEqual(Topic.objects.filter(forum=self.beta_forum).count(), 1)
        self.assertTrue(PublishableContent.objects.get(pk=self.tuto.pk).beta_topic is not None)
        self.assertEqual(PrivateTopic.objects.filter(author=self.user_author).count(), 1)
        # check if there is a new topic
        beta_topic = PublishableContent.objects.get(pk=self.tuto.pk).beta_topic
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(self.user_author, beta_topic, is_active=True))
        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 1)
        self.assertEqual(beta_topic.tags.count(), 1)
        self.assertEqual(beta_topic.tags.first().title, sometag.title)
        # check signal is emitted
        self.assertEqual(beta_management.send.call_count, 1)
        self.assertEqual(beta_management.send.call_args[1]["action"], "activate")

        # test if second author follow the topic
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(second_author, beta_topic, is_active=True))
        self.assertEqual(TopicRead.objects.filter(topic__pk=beta_topic.pk, user__pk=second_author.pk).count(), 1)

        # test access for public
        self.client.logout()
        url = reverse("content:beta-view", args=[self.tuto.pk, self.tuto.slug])
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 302)  # (get 302: no access to beta for public)

        # test access for guest
        self.client.force_login(self.user_guest)
        url = reverse("content:beta-view", args=[tuto.pk, tuto.slug])
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": tuto.slug,
            "container_slug": self.part1.slug,
        }
        url = reverse("content:beta-view-container", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": tuto.slug,
            "parent_container_slug": self.part1.slug,
            "container_slug": self.chapter1.slug,
        }
        url = reverse("content:beta-view-container", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # change beta version
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse(
                "content:edit-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            {
                "title": "Un autre titre",
                "introduction": "Introduire la chose",
                "conclusion": "Et terminer sur un truc bien",
                "last_hash": self.part1.compute_hash(),
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertNotEqual(current_sha_beta, tuto.sha_draft)

        # add third author:
        third_author = ProfileFactory().user
        tuto.authors.add(third_author)
        tuto.save()

        self.assertIsNone(TopicAnswerSubscription.objects.get_existing(third_author, beta_topic, is_active=True))
        self.assertEqual(TopicRead.objects.filter(topic__pk=beta_topic.pk, user__pk=third_author.pk).count(), 0)

        # change beta:
        old_sha_beta = current_sha_beta
        current_sha_beta = tuto.sha_draft
        result = self.client.post(
            reverse("content:set-beta", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"version": current_sha_beta},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertEqual(tuto.sha_beta, current_sha_beta)

        # No new message added since the last time, because the last message
        # was posted since less than 15 minutes ago.

        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 1)

        # test if third author follows the topic
        self.assertIsNotNone(TopicAnswerSubscription.objects.get_existing(third_author, beta_topic, is_active=True))
        self.assertEqual(TopicRead.objects.filter(topic__pk=beta_topic.pk, user__pk=third_author.pk).count(), 1)

        # then test for guest
        self.client.force_login(self.user_guest)
        url = reverse("content:beta-view", args=[tuto.pk, tuto.slug])
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)  # ok for the new version

        # inactive beta
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("content:inactive-beta", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"version": current_sha_beta},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 2)  # a new message was added !
        self.assertTrue(Topic.objects.get(pk=beta_topic.pk).is_locked)  # beta was inactived, so topic is locked !
        # check signal is emitted
        self.assertEqual(beta_management.send.call_count, 3)
        self.assertEqual(beta_management.send.call_args[1]["action"], "deactivate")

        # then test for guest
        self.client.force_login(self.user_guest)
        url = reverse("content:beta-view", args=[tuto.pk, tuto.slug])
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 404)

        # reactive beta
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("content:set-beta", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"version": old_sha_beta},  # with a different version than the draft one
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertEqual(tuto.sha_beta, old_sha_beta)

        # No new message added since the last time, because the last message
        # was posted since less than 15 minutes ago.

        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 3)  # a new message was added !
        self.assertFalse(Topic.objects.get(pk=beta_topic.pk).is_locked)  # not locked anymore

        # then test for guest
        self.client.force_login(self.user_guest)
        url = reverse("content:beta-view", args=[tuto.pk, tuto.slug])
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)  # access granted

    def test_beta_helps(self):
        """Check that editorial helps are visible on the beta"""

        # login with author
        self.client.force_login(self.user_author)

        # create and add help
        help = HelpWritingFactory()
        help.save()

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        tuto.helps.add(help)
        tuto.save()

        # activate beta
        result = self.client.post(
            reverse("content:set-beta", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"version": tuto.sha_draft},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # check that the information is displayed on the beta page
        result = self.client.get(reverse("content:beta-view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, _("L’auteur de ce contenu recherche"))
        # and on a container
        result = self.client.get(
            reverse(
                "content:beta-view-container",
                kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug},
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, _("L’auteur de ce contenu recherche"))

    def test_beta_external(self):
        """
        Activating the beta shall work even with a bot in the authors.
        Check a non-regression on a bug where exceptions were raised when activating
        the beta with "Auteur externe" among the authors.
        """
        self.client.force_login(self.user_author)

        self.tuto.authors.add(self.external)

        result = self.client.post(
            reverse("content:set-beta", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}),
            {"version": self.tuto.sha_draft},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
