import datetime
from copy import deepcopy
from json import loads

from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds import json_handler
from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.mp.models import PrivateTopic, is_privatetopic_unread
from zds.notification.models import ContentReactionAnswerSubscription, Notification
from zds.tutorialv2.models.database import (
    ContentReaction,
    ContentRead,
    PickListOperation,
    PublishableContent,
    PublishedContent,
    Validation,
)
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ContentReactionFactory,
    ExtractFactory,
    HelpWritingFactory,
    PublishableContentFactory,
    PublishedContentFactory,
)
from zds.utils.header_notifications import get_header_notifications
from zds.utils.models import Alert, Hat, Tag
from zds.utils.tests.factories import CategoryFactory, LicenceFactory, SubCategoryFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"
overridden_zds_app["content"]["extra_content_generation_policy"] = "NOTHING"


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "media-test")
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(SEARCH_ENABLED=False)
class PublishedContentTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        overridden_zds_app["content"]["default_licence_pk"] = LicenceFactory().pk

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        overridden_zds_app["member"]["bot_account"] = self.mas.username

        bot = Group(name=overridden_zds_app["member"]["bot_group"])
        bot.save()
        self.external = UserFactory(username=overridden_zds_app["member"]["external_account"], password="anything")
        self.external.groups.add(bot)
        self.external.save()
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.anonymous.groups.add(bot)
        self.anonymous.save()

        self.beta_forum = ForumFactory(
            pk=overridden_zds_app["forum"]["beta_forum_id"],
            category=ForumCategoryFactory(position=1),
            position_in_category=1,
        )  # ensure that the forum, for the beta versions, is created

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        self.hat, _ = Hat.objects.get_or_create(name__iexact="A hat", defaults={"name": "A hat"})
        self.user_guest.profile.hats.add(self.hat)

        # create a tutorial
        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode="W")
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        # fill it with one part, containing one chapter, containing one extract
        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

        # then, publish it !
        version = self.tuto_draft.current_version
        self.published = publish_content(self.tuto, self.tuto_draft, is_major_update=True)

        self.tuto.sha_public = version
        self.tuto.sha_draft = version
        self.tuto.public_version = self.published
        self.tuto.save()

    def test_published(self):
        """Just a small test to ensure that the setUp() function produce a proper published content"""

        result = self.client.get(reverse("tutorial:view", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}))
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.client.force_login(self.user_guest)

        result = self.client.get(reverse("tutorial:view", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}))
        self.assertEqual(result.status_code, 200)

    def test_public_access(self):
        """Test that everybody have access to a content after its publication"""

        text_validation = "Valide moi ce truc, please !"
        text_publication = "Aussi tôt dit, aussi tôt fait !"

        # 1. Article:
        article = PublishableContentFactory(type="ARTICLE")

        article.authors.add(self.user_author)
        UserGalleryFactory(gallery=article.gallery, user=self.user_author, mode="W")
        article.licence = self.licence
        article.save()

        # populate the article
        article_draft = article.load_version()
        ExtractFactory(container=article_draft, db_object=article)
        ExtractFactory(container=article_draft, db_object=article)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": article.pk, "slug": article.slug}),
            {"text": text_validation, "version": article_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=article).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=article).first()
        self.assertIsNotNone(published)

        # test access to staff
        result = self.client.get(reverse("article:view", kwargs={"pk": article.pk, "slug": article_draft.slug}))
        self.assertEqual(result.status_code, 200)

        # test access to public
        self.client.logout()
        result = self.client.get(reverse("article:view", kwargs={"pk": article.pk, "slug": article_draft.slug}))
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.client.force_login(self.user_guest)
        result = self.client.get(reverse("article:view", kwargs={"pk": article.pk, "slug": article_draft.slug}))
        self.assertEqual(result.status_code, 200)

        # 2. middle-size tutorial (just to test the access to chapters)
        midsize_tuto = PublishableContentFactory(type="TUTORIAL")

        midsize_tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=midsize_tuto.gallery, user=self.user_author, mode="W")
        midsize_tuto.licence = self.licence
        midsize_tuto.save()

        # populate the midsize_tuto
        midsize_tuto_draft = midsize_tuto.load_version()
        chapter1 = ContainerFactory(parent=midsize_tuto_draft, db_object=midsize_tuto)
        ExtractFactory(container=chapter1, db_object=midsize_tuto)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto.slug}),
            {"text": text_validation, "version": midsize_tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=midsize_tuto).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=midsize_tuto).first()
        self.assertIsNotNone(published)

        # test access to staff
        result = self.client.get(
            reverse("tutorial:view", kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto_draft.slug})
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto_draft.slug, "container_slug": chapter1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        # test access to public
        self.client.logout()
        result = self.client.get(
            reverse("tutorial:view", kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto_draft.slug})
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto_draft.slug, "container_slug": chapter1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.client.force_login(self.user_guest)
        result = self.client.get(
            reverse("tutorial:view", kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto_draft.slug})
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": midsize_tuto.pk, "slug": midsize_tuto_draft.slug, "container_slug": chapter1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        # 3. a big tutorial (just to test the access to parts and chapters)
        bigtuto = PublishableContentFactory(type="TUTORIAL")

        bigtuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=bigtuto.gallery, user=self.user_author, mode="W")
        bigtuto.licence = self.licence
        bigtuto.save()

        # populate the bigtuto
        bigtuto_draft = bigtuto.load_version()
        part1 = ContainerFactory(parent=bigtuto_draft, db_object=bigtuto)
        chapter1 = ContainerFactory(parent=part1, db_object=bigtuto)
        ExtractFactory(container=chapter1, db_object=bigtuto)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": bigtuto.pk, "slug": bigtuto.slug}),
            {"text": text_validation, "version": bigtuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=bigtuto).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=bigtuto).first()
        self.assertIsNotNone(published)

        # test access to staff
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug, "container_slug": part1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": bigtuto.pk,
                    "slug": bigtuto_draft.slug,
                    "parent_container_slug": part1.slug,
                    "container_slug": chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 200)

        # test access to public
        self.client.logout()
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug, "container_slug": part1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": bigtuto.pk,
                    "slug": bigtuto_draft.slug,
                    "parent_container_slug": part1.slug,
                    "container_slug": chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.client.force_login(self.user_guest)
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug, "container_slug": part1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": bigtuto.pk,
                    "slug": bigtuto_draft.slug,
                    "parent_container_slug": part1.slug,
                    "container_slug": chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 200)

        # just for the fun of it, lets then revoke publication
        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": bigtuto.pk, "slug": bigtuto.slug}),
            {"text": "Pour le fun", "version": bigtuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # now, let's get a whole bunch of good old fashioned 404 (and not 403 or 302 !!)
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug, "container_slug": part1.slug},
            )
        )
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": bigtuto.pk,
                    "slug": bigtuto_draft.slug,
                    "parent_container_slug": part1.slug,
                    "container_slug": chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 404)

        # test access to public
        self.client.logout()
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug, "container_slug": part1.slug},
            )
        )
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": bigtuto.pk,
                    "slug": bigtuto_draft.slug,
                    "parent_container_slug": part1.slug,
                    "container_slug": chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 404)

        # test access for guest user
        self.client.force_login(self.user_guest)

        result = self.client.get(reverse("tutorial:view", kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": bigtuto.pk, "slug": bigtuto_draft.slug, "container_slug": part1.slug},
            )
        )
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": bigtuto.pk,
                    "slug": bigtuto_draft.slug,
                    "parent_container_slug": part1.slug,
                    "container_slug": chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 404)

    def test_add_note(self):
        message_to_post = "la ZEP-12"

        self.client.force_login(self.user_guest)

        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.published.content.pk}",
            {"text": message_to_post, "last_note": 0, "with_hat": self.hat.pk},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(ContentReaction.objects.latest("pubdate").hat, self.hat)

        reactions = ContentReaction.objects.all()
        self.assertEqual(len(reactions), 1)
        self.assertEqual(reactions[0].text, message_to_post)

        reads = ContentRead.objects.filter(user=self.user_guest).all()
        self.assertEqual(len(reads), 1)
        self.assertEqual(reads[0].content.pk, self.tuto.pk)
        self.assertEqual(reads[0].note.pk, reactions[0].pk)

        self.assertEqual(
            self.client.get(reverse("tutorial:view", args=[self.tuto.pk, self.tuto.slug])).status_code, 200
        )
        result = self.client.post(
            reverse("content:add-reaction") + f"?clementine={self.published.content.pk}",
            {"text": message_to_post, "last_note": "0"},
            follow=True,
        )
        self.assertEqual(result.status_code, 404)

        # visit the tutorial trigger the creation of a ContentRead
        self.client.force_login(self.user_staff)

        self.assertEqual(
            self.client.get(reverse("tutorial:view", args=[self.tuto.pk, self.tuto.slug])).status_code, 200
        )

        reads = ContentRead.objects.filter(user=self.user_staff).all()
        # simple visit does not trigger follow but remembers reading
        self.assertEqual(len(reads), 1)
        interventions = [
            post["url"] for post in get_header_notifications(self.user_staff)["general_notifications"]["list"]
        ]
        self.assertTrue(reads.first().note.get_absolute_url() not in interventions)

        # login with author
        self.client.force_login(self.user_author)

        # test preview (without JS)
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.published.content.pk}",
            {"text": message_to_post, "last_note": reactions[0].pk, "preview": True},
        )
        self.assertEqual(result.status_code, 200)

        self.assertTrue(message_to_post in result.context["text"])

        # test preview (with JS)
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.published.content.pk}",
            {"text": message_to_post, "last_note": reactions[0].pk, "preview": True},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        result_string = "".join(a.decode() for a in result.streaming_content)
        self.assertTrue(message_to_post in result_string)

        # test quoting (without JS)
        result = self.client.get(
            reverse("content:add-reaction") + f"?pk={self.published.content.pk}&cite={reactions[0].pk}"
        )
        self.assertEqual(result.status_code, 200)

        text_field_value = result.context["form"].initial["text"]

        self.assertTrue(message_to_post in text_field_value)
        self.assertTrue(self.user_guest.username in text_field_value)
        self.assertTrue(reactions[0].get_absolute_url() in text_field_value)

        # test quoting (with JS)
        result = self.client.get(
            reverse("content:add-reaction") + f"?pk={self.published.content.pk}&cite={reactions[0].pk}",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(result.status_code, 200)
        json = {}

        try:
            json = json_handler.loads("".join(a.decode() for a in result.streaming_content))
        except Exception as e:  # broad exception on purpose
            self.assertEqual(e, "")

        self.assertTrue("text" in json)
        text_field_value = json["text"]

        self.assertTrue(message_to_post in text_field_value)
        self.assertTrue(self.user_guest.username in text_field_value)
        self.assertTrue(reactions[0].get_absolute_url() in text_field_value)

        # test that if the wrong last_note is given, user get a message
        self.assertEqual(ContentReaction.objects.count(), 1)

        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.published.content.pk}",
            {"text": message_to_post, "last_note": -1},  # wrong pk
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        self.assertEqual(ContentReaction.objects.count(), 1)  # no new reaction has been posted
        self.assertTrue(result.context["newnote"])  # message appears !

    def test_hide_reaction(self):
        text_hidden = (
            "Ever notice how you come across somebody once in a while you shouldn't have fucked with? That's me."
        )

        self.client.force_login(self.user_guest)

        self.client.post(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}",
            {"text": "message", "last_note": "0"},
            follow=True,
        )

        self.client.force_login(self.user_staff)

        reaction = ContentReaction.objects.filter(related_content__pk=self.tuto.pk).first()

        result = self.client.post(
            reverse("content:hide-reaction", args=[reaction.pk]), {"text_hidden": text_hidden}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        reaction = ContentReaction.objects.get(pk=reaction.pk)
        self.assertFalse(reaction.is_visible)
        self.assertEqual(reaction.text_hidden, text_hidden[:80])
        self.assertEqual(reaction.editor, self.user_staff)

        # test that someone else is not abble to quote the text
        self.client.force_login(self.user_guest)

        result = self.client.get(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}&cite={reaction.pk}", follow=False
        )
        self.assertEqual(result.status_code, 403)  # unable to quote a reaction if hidden

        # then, unhide it !
        self.client.force_login(self.user_guest)

        result = self.client.post(reverse("content:show-reaction", args=[reaction.pk]), follow=False)

        self.assertEqual(result.status_code, 302)

        reaction = ContentReaction.objects.get(pk=reaction.pk)
        self.assertTrue(reaction.is_visible)

    def test_alert_reaction(self):
        self.client.force_login(self.user_guest)

        self.client.post(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}",
            {"text": "message", "last_note": "0"},
            follow=True,
        )
        reaction = ContentReaction.objects.filter(related_content__pk=self.tuto.pk).first()
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("content:alert-reaction", args=[reaction.pk]),
            {"signal_text": "No. Try not. Do... or do not. There is no try."},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first())
        result = self.client.post(
            reverse("content:resolve-reaction"),
            {
                "alert_pk": Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first().pk,
                "text": "No. Try not. Do... or do not. There is no try.",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 403)
        self.client.force_login(self.user_staff)
        result = self.client.post(
            reverse("content:resolve-reaction"),
            {
                "alert_pk": Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first().pk,
                "text": "Much to learn, you still have.",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertIsNone(
            Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk, solved=False).first()
        )
        reaction = ContentReaction.objects.filter(related_content__pk=self.tuto.pk).first()

        # test that edition of a comment with an alert by an admin also solve the alert
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("content:alert-reaction", args=[reaction.pk]),
            {"signal_text": "No. Try not. Do... or do not. There is no try."},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(
            Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk, solved=False).first()
        )

        self.client.force_login(self.user_staff)
        result = self.client.post(
            reverse("content:update-reaction") + f"?message={reaction.pk}&pk={self.tuto.pk}",
            {"text": "Much to learn, you still have."},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertIsNone(
            Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk, solved=False).first()
        )

    def test_warn_typo_without_accessible_author(self):
        self.client.force_login(self.user_guest)
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={self.tuto.pk}",
            {
                "pk": self.tuto.pk,
                "version": self.published.sha_public,
                "text": "This is how they controlled it. "
                "It took us 15 years and three supercomputers to MacGyver a system for the gate on Earth. ",
                "target": "",
            },
            follow=True,
        )
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(PrivateTopic.objects.filter(participants__in=[self.external]).first())

        # add a banned user:
        user_banned = ProfileFactory(
            can_write=False,
            end_ban_write=datetime.date(2048, 0o1, 0o1),
            can_read=False,
            end_ban_read=datetime.date(2048, 0o1, 0o1),
        )
        self.tuto.authors.add(user_banned.user)
        self.tuto.save()

        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={self.tuto.pk}",
            {
                "pk": self.tuto.pk,
                "version": self.published.sha_public,
                "text": "This is how they controlled it. "
                "It took us 15 years and three supercomputers to MacGyver a system for the gate on Earth. ",
                "target": "",
            },
            follow=True,
        )
        self.assertIsNone(PrivateTopic.objects.filter(participants__in=[self.external]).first())
        self.assertEqual(result.status_code, 200)

    def test_find_tutorial_or_article(self):
        """test the behavior of `article:find-article` and `content-find-tutorial` urls"""

        self.client.force_login(self.user_author)

        tuto_in_beta = PublishableContentFactory(type="TUTORIAL")
        tuto_in_beta.authors.add(self.user_author)
        tuto_in_beta.sha_beta = "whatever"
        tuto_in_beta.save()

        tuto_draft = PublishableContentFactory(type="TUTORIAL")
        tuto_draft.authors.add(self.user_author)
        tuto_draft.save()

        article_in_validation = PublishableContentFactory(type="ARTICLE")
        article_in_validation.authors.add(self.user_author)
        article_in_validation.sha_validation = "whatever"  # the article is in validation
        article_in_validation.save()

        # test without filters
        response = self.client.get(reverse("tutorial:find-tutorial", args=[self.user_author.username]), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 3)  # 3 tutorials

        response = self.client.get(reverse("article:find-article", args=[self.user_author.username]), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 1)  # 1 article

        # test a non-existing filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=whatever", follow=False
        )
        self.assertEqual(404, response.status_code)  # this filter does not exists !

        # test 'redaction' filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=redaction", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # one tutorial in redaction
        self.assertEqual(contents[0].pk, tuto_draft.pk)

        response = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=redaction", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 0)  # no article in redaction

        # test beta filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=beta", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # one tutorial in beta
        self.assertEqual(contents[0].pk, tuto_in_beta.pk)

        response = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=beta", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 0)  # no article in beta

        # test validation filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=validation", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 0)  # no tutorial in validation

        response = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=validation", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 1)  # one article in validation
        self.assertEqual(contents[0].pk, article_in_validation.pk)

        # test public filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=public", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # one published tutorial
        self.assertEqual(contents[0].pk, self.tuto.pk)

        response = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=public", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 0)  # no published article

        self.client.logout()

        # test validation filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=validation", follow=False
        )
        self.assertEqual(403, response.status_code)  # not allowed for public

        # test redaction filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=redaction", follow=False
        )
        self.assertEqual(403, response.status_code)  # not allowed for public

        # test beta filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=beta", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # one tutorial in beta
        self.assertEqual(contents[0].pk, tuto_in_beta.pk)

        response = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=beta", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 0)  # no article in beta

        # test public filter
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=public", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # one published tutorial
        self.assertEqual(contents[0].pk, self.tuto.pk)

        response = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=public", follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 0)  # no published article

        # test no filter → same answer as 'public'
        response = self.client.get(reverse("tutorial:find-tutorial", args=[self.user_author.username]), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # one published tutorial
        self.assertEqual(contents[0].pk, self.tuto.pk)

        response = self.client.get(reverse("article:find-article", args=[self.user_author.username]), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["articles"]
        self.assertEqual(len(contents), 0)  # no published article

        self.client.force_login(self.user_staff)

        response = self.client.get(reverse("tutorial:find-tutorial", args=[self.user_author.username]), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["tutorials"]
        self.assertEqual(len(contents), 1)  # 1 published tutorial by user_author !

        # staff can use all filters without a 403 !

        # test validation filter:
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=validation", follow=False
        )
        self.assertEqual(403, response.status_code)

        # test redaction filter:
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=redaction", follow=False
        )
        self.assertEqual(403, response.status_code)

        # test beta filter:
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=beta", follow=False
        )
        self.assertEqual(200, response.status_code)

        # test redaction filter:
        response = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=redaction", follow=False
        )
        self.assertEqual(403, response.status_code)

    def test_last_reactions(self):
        """Test and ensure the behavior of last_read_note() and first_unread_note().

        Note: for a unknown reason, `get_current_user()` does not return the good answer if a page is not
        visited before, therefore this test will visit the index after each login (because :p)"""

        # login with guest
        self.client.force_login(self.user_guest)

        result = self.client.get(reverse("pages-index"))  # go to whatever page
        self.assertEqual(result.status_code, 200)

        self.assertEqual(ContentRead.objects.filter(user=self.user_guest).count(), 0)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # no reaction yet:
        self.assertIsNone(tuto.last_read_note())
        self.assertIsNone(tuto.first_unread_note())
        self.assertIsNone(tuto.first_note())

        # post a reaction
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}",
            {"text": "message", "last_note": "0"},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        reactions = ContentReaction.objects.filter(related_content=self.tuto).all()
        self.assertEqual(len(reactions), 1)

        self.assertEqual(ContentRead.objects.filter(user=self.user_guest).count(), 1)  # last reaction read

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        self.assertEqual(tuto.first_note(), reactions[0])
        self.assertEqual(tuto.last_read_note(), reactions[0])
        self.assertEqual(tuto.first_unread_note(), reactions[0])  # if no next reaction, first unread=last read

        self.client.logout()

        # login with author (could be staff, we don't care in this test)
        self.client.force_login(self.user_author)

        result = self.client.get(reverse("pages-index"))  # go to whatever page
        self.assertEqual(result.status_code, 200)

        self.assertIsNone(
            ContentReactionAnswerSubscription.objects.get_existing(user=self.user_author, content_object=tuto)
        )

        self.assertEqual(tuto.last_read_note(), reactions[0])  # if never read, last note=first note
        self.assertEqual(tuto.first_unread_note(), reactions[0])

        # post another reaction
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}",
            {"text": "message", "last_note": reactions[0].pk},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        reactions = list(ContentReaction.objects.filter(related_content=self.tuto).all())
        self.assertEqual(len(reactions), 2)

        self.assertTrue(
            ContentReactionAnswerSubscription.objects.get_existing(user=self.user_author, content_object=tuto).is_active
        )

        self.assertEqual(tuto.first_note(), reactions[0])  # first note is still first note
        self.assertEqual(tuto.last_read_note(), reactions[1])
        self.assertEqual(tuto.first_unread_note(), reactions[1])

        # test if not connected
        self.client.logout()

        result = self.client.get(reverse("pages-index"))  # go to whatever page
        self.assertEqual(result.status_code, 200)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.last_read_note(), reactions[0])  # last read note = first note
        self.assertEqual(tuto.first_unread_note(), reactions[0])  # first unread note = first note

        # visit tutorial
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": tuto.pk, "slug": tuto.slug}))
        self.assertEqual(result.status_code, 200)

        # but nothing has changed (because not connected = no notifications and no 'tracking')
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.last_read_note(), reactions[0])  # last read note = first note
        self.assertEqual(tuto.first_unread_note(), reactions[0])  # first unread note = first note

        # re-login with guest
        self.client.force_login(self.user_guest)

        result = self.client.get(reverse("pages-index"))  # go to whatever page
        self.assertEqual(result.status_code, 200)

        self.assertEqual(ContentRead.objects.filter(user=self.user_guest).count(), 1)  # already read first reaction
        reads = ContentRead.objects.filter(user=self.user_guest).all()

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.last_read_note(), reactions[0])
        self.assertEqual(tuto.first_unread_note(), reactions[1])  # new reaction of author is unread

        # visit tutorial to get rid of the notification
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": tuto.pk, "slug": tuto.slug}))
        self.assertEqual(result.status_code, 200)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.last_read_note(), reactions[1])  # now, new reaction is read !
        self.assertEqual(tuto.first_unread_note(), reactions[1])

        self.assertEqual(ContentRead.objects.filter(user=self.user_guest).count(), 1)
        self.assertNotEqual(reads, ContentRead.objects.filter(user=self.user_guest).all())  # not the same message

        self.client.logout()

        result = self.client.get(reverse("pages-index"))  # go to whatever page
        self.assertEqual(result.status_code, 200)

    def test_reaction_follow_email(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.assertEqual(0, len(mail.outbox))

        profile = ProfileFactory()
        self.client.force_login(profile.user)
        response = self.client.post(reverse("content:follow-reactions", args=[self.tuto.pk]), {"email": "1"})
        self.assertEqual(302, response.status_code)

        self.assertIsNotNone(
            ContentReactionAnswerSubscription.objects.get_existing(
                profile.user, self.tuto, is_active=True, by_email=True
            )
        )

        self.client.logout()

        self.client.force_login(self.user_author)

        # post another reaction
        self.client.post(
            reverse("content:add-reaction") + f"?pk={self.tuto.pk}",
            {"text": "message", "last_note": "0"},
            follow=True,
        )

        self.assertEqual(1, len(mail.outbox))

    def test_note_with_bad_param(self):
        self.client.force_login(self.user_staff)
        url_template = reverse("content:update-reaction") + "?pk={}&message={}"
        result = self.client.get(url_template.format(self.tuto.pk, 454545665895123))
        self.assertEqual(404, result.status_code)
        reaction = ContentReaction(related_content=self.tuto, author=self.user_guest, position=1)
        reaction.update_content("blah")
        reaction.save()
        self.tuto.last_note = reaction
        self.tuto.save()
        result = self.client.get(url_template.format(861489632, reaction.pk))
        self.assertEqual(404, result.status_code)

    def test_cant_edit_not_owned_note(self):
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        new_user = ProfileFactory().user
        new_reaction = ContentReaction(related_content=article, position=1)
        new_reaction.author = self.user_guest
        new_reaction.update_content("I will find you.")

        new_reaction.save()
        self.client.force_login(new_user)
        resp = self.client.get(reverse("content:update-reaction") + f"?message={new_reaction.pk}&pk={article.pk}")
        self.assertEqual(403, resp.status_code)
        resp = self.client.post(
            reverse("content:update-reaction") + f"?message={new_reaction.pk}&pk={article.pk}",
            {"text": "I edited it"},
        )
        self.assertEqual(403, resp.status_code)

    def test_quote_note(self):
        """Ensure the behavior of the `&cite=xxx` parameter on 'content:add-reaction'"""

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        text = (
            "À force de temps, de patience et de crachats, "
            "on met un pépin de callebasse dans le derrière d'un moustique (proverbe créole)"
        )

        # add note :
        reaction = ContentReaction(related_content=tuto, position=1)
        reaction.author = self.user_guest
        reaction.update_content(text)
        reaction.save()

        self.client.force_login(self.user_author)

        # cite note
        result = self.client.get(reverse("content:add-reaction") + f"?pk={tuto.pk}&cite={reaction.pk}", follow=True)
        self.assertEqual(200, result.status_code)

        self.assertTrue(text in result.context["form"].initial["text"])  # ok, text quoted !

        # cite with a abnormal parameter raises 404
        result = self.client.get(
            reverse("content:add-reaction") + "?pk={}&cite={}".format(tuto.pk, "lililol"), follow=True
        )
        self.assertEqual(404, result.status_code)

        # cite not existing note just gives the form empty
        result = self.client.get(reverse("content:add-reaction") + f"?pk={tuto.pk}&cite={99999999}", follow=True)
        self.assertEqual(200, result.status_code)

        self.assertTrue("text" not in result.context["form"])  # nothing quoted, so no text cited

        # it's not possible to cite an hidden note (get 403)
        reaction.is_visible = False
        reaction.save()

        result = self.client.get(reverse("content:add-reaction") + f"?pk={tuto.pk}&cite={reaction.pk}", follow=True)
        self.assertEqual(403, result.status_code)

    def test_cant_view_private_even_if_draft_is_equal_to_public(self):
        content = PublishedContentFactory(author_list=[self.user_author])
        self.client.force_login(self.user_guest)
        resp = self.client.get(reverse("content:view", args=[content.pk, content.slug]))
        self.assertEqual(403, resp.status_code)

    def test_republish_with_different_slug(self):
        """Ensure that a new PublishedContent object is created and well filled"""

        self.assertEqual(PublishedContent.objects.count(), 1)

        old_published = PublishedContent.objects.filter(content__pk=self.tuto.pk).first()
        self.assertIsNotNone(old_published)
        self.assertFalse(old_published.must_redirect)

        # connect with author:
        self.client.force_login(self.user_author)

        # change title
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_slug = tuto.slug

        result = self.client.post(
            reverse("content:edit-title", args=[tuto.pk]),
            {"title": "{self.tuto.title} (modified)"},  # will change the slug
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertNotEqual(tuto.slug, old_slug)

        # ask validation
        text_validation = "Valide moi ce truc, please !"
        text_publication = "Aussi tôt dit, aussi tôt fait !"
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": tuto.sha_draft},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content__pk=tuto.pk).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": False},  # minor modification (just the title)
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 2)

        old_published = PublishedContent.objects.get(pk=old_published.pk)
        self.assertIsNotNone(old_published)  # still exists
        self.assertTrue(old_published.must_redirect)  # do redirection if any
        self.assertIsNone(old_published.update_date)
        result = self.client.get(old_published.get_absolute_url_online(), follow=False)
        self.assertEqual(result.status_code, 301)
        # extra contents are also redirected
        result = self.client.get(old_published.get_absolute_url_md(), follow=False)
        self.assertEqual(result.status_code, 301)
        new_published = PublishedContent.objects.filter(content__pk=self.tuto.pk).last()
        self.assertIsNotNone(new_published)  # new version exists
        self.assertNotEqual(old_published.pk, new_published.pk)  # not the old one
        self.assertEqual(new_published.publication_date, old_published.publication_date)  # keep publication date
        self.assertIsNotNone(new_published.update_date)  # ... But is updated !

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.public_version.pk, new_published.pk)

    def test_logical_article_pagination(self):
        """Test that the past is 'left' and the future is 'right', or in other word that the good article
        are given to pagination and not the opposite"""

        article1 = PublishedContentFactory(type="ARTICLE")

        # force 'article1' to be the first one by setting a publication date equals to one hour before the test
        article1.public_version.publication_date = datetime.datetime.now() - datetime.timedelta(0, 1)
        article1.public_version.save()

        article2 = PublishedContentFactory(type="ARTICLE")

        self.assertEqual(PublishedContent.objects.count(), 3)  # both articles have been published

        # visit article 1 (so article2 is next)
        result = self.client.get(reverse("article:view", kwargs={"pk": article1.pk, "slug": article1.slug}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["next_content"].pk, article2.public_version.pk)
        self.assertIsNone(result.context["previous_content"])

        # visit article 2 (so article1 is previous)
        result = self.client.get(reverse("article:view", kwargs={"pk": article2.pk, "slug": article2.slug}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context["previous_content"].pk, article1.public_version.pk)
        self.assertIsNone(result.context["next_content"])

    def test_validation_list_has_good_title(self):
        # aka fix 3172
        tuto = PublishableContentFactory(author_list=[self.user_author], type="TUTORIAL")
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("validation:ask", args=[tuto.pk, tuto.slug]),
            {"text": "something good", "version": tuto.sha_draft},
            follow=False,
        )
        old_title = tuto.title
        new_title = "a brand new title"
        self.client.post(
            reverse("content:edit-title", args=[tuto.pk]),
            {"title": new_title},
            follow=False,
        )
        self.client.logout()
        self.client.force_login(self.user_staff)
        result = self.client.get(reverse("validation:list") + "?type=tuto")
        self.assertIn(old_title, str(result.content))
        self.assertNotIn(new_title, str(result.content))

    def test_public_authors_versioned(self):
        published = PublishedContentFactory(author_list=[self.user_author])
        other_author = ProfileFactory()
        published.authors.add(other_author.user)
        published.save()
        response = self.client.get(published.get_absolute_url_online())
        self.assertIn(self.user_author.username, str(response.content))
        self.assertNotIn(other_author.user.username, str(response.content))
        self.assertEqual(0, len(other_author.get_public_contents()))

    def test_unpublish_with_title_change(self):
        # aka 3329
        article = PublishedContentFactory(type="ARTICLE", author_list=[self.user_author], licence=self.licence)
        registered_validation = Validation(
            content=article,
            version=article.sha_draft,
            status="ACCEPT",
            comment_authors="bla",
            comment_validator="bla",
            date_reserve=datetime.datetime.now(),
            date_proposition=datetime.datetime.now(),
            date_validation=datetime.datetime.now(),
        )
        registered_validation.save()
        self.client.force_login(self.user_staff)
        self.client.post(
            reverse("content:edit-title", args=[article.pk]),
            {"title": "new title so that everything explode"},
            follow=False,
        )
        public_count = PublishedContent.objects.count()
        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": article.pk, "slug": article.public_version.content_public_slug}),
            {"text": "This content was bad", "version": article.public_version.sha_public},
            follow=False,
        )
        self.assertEqual(302, result.status_code)
        self.assertEqual(public_count - 1, PublishedContent.objects.count())
        self.assertEqual("PENDING", Validation.objects.get(pk=registered_validation.pk).status)

    def test_unpublish_unregistered_author(self):
        article = PublishedContentFactory(type="ARTICLE", author_list=[self.user_author], licence=self.licence)
        registered_validation = Validation(
            content=article,
            version=article.sha_draft,
            status="ACCEPT",
            comment_authors="bla",
            comment_validator="bla",
            date_reserve=datetime.datetime.now(),
            date_proposition=datetime.datetime.now(),
            date_validation=datetime.datetime.now(),
        )
        registered_validation.save()

        self.client.force_login(self.user_author)
        result = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
        self.assertEqual(result.status_code, 302)

        self.client.force_login(self.user_staff)
        public_count = PublishedContent.objects.count()
        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": article.pk, "slug": article.public_version.content_public_slug}),
            {"text": "This content was bad", "version": article.public_version.sha_public},
            follow=False,
        )
        self.assertEqual(302, result.status_code)
        self.assertEqual(public_count - 1, PublishedContent.objects.count())
        self.assertEqual("PENDING", Validation.objects.get(pk=registered_validation.pk).status)

    def test_unpublish_with_empty_subscription(self):
        article = PublishedContentFactory(type="ARTICLE", author_list=[self.user_author], licence=self.licence)
        registered_validation = Validation(
            content=article,
            version=article.sha_draft,
            status="ACCEPT",
            comment_authors="bla",
            comment_validator="bla",
            date_reserve=datetime.datetime.now(),
            date_proposition=datetime.datetime.now(),
            date_validation=datetime.datetime.now(),
        )
        registered_validation.save()
        subscriber = ProfileFactory().user
        self.client.force_login(subscriber)
        resp = self.client.post(reverse("content:follow-reactions", args=[article.pk]), {"follow": True})
        self.assertEqual(302, resp.status_code)
        public_count = PublishedContent.objects.count()
        self.client.logout()
        self.client.force_login(self.user_staff)
        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": article.pk, "slug": article.public_version.content_public_slug}),
            {"text": "This content was bad", "version": article.public_version.sha_public},
            follow=False,
        )
        self.assertEqual(302, result.status_code)
        self.assertEqual(public_count - 1, PublishedContent.objects.count())
        self.assertEqual(ContentReactionAnswerSubscription.objects.filter(is_active=False).count(), 1)

    def test_validation_history(self):
        published = PublishedContentFactory(author_list=[self.user_author])
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("content:edit-subtitle", args=[published.pk]),
            {"subtitle": "Sous-titre qui fait une nouvelle version"},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": published.pk, "slug": published.slug}),
            {"text": "abcdefg", "version": published.load_version().current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)
        self.client.logout()
        self.client.force_login(self.user_staff)
        result = self.client.get(reverse("validation:list") + "?type=tuto")
        self.assertIn('class="update_content"', str(result.content))

    def test_validation_history_for_new_content(self):
        publishable = PublishableContentFactory(author_list=[self.user_author])
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": publishable.pk, "slug": publishable.slug}),
            {"text": "abcdefg", "version": publishable.load_version().current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)
        self.client.logout()
        self.client.force_login(self.user_staff)
        result = self.client.get(reverse("validation:list") + "?type=tuto")
        self.assertNotIn('class="update_content"', str(result.content))

    def test_ask_validation_update(self):
        """
        Test AskValidationView.
        """
        text_validation = "La validation on vous aime !"
        content = PublishableContentFactory(author_list=[self.user_author], type="ARTICLE")
        content.save()
        content_draft = content.load_version()

        self.assertEqual(Validation.objects.count(), 0)

        # login with user and ask validation
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": content_draft.pk, "slug": content_draft.slug}),
            {"text": text_validation, "version": content_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        # login with staff and reserve the content
        self.client.force_login(self.user_staff)
        validation = Validation.objects.filter(content=content).last()
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # login with user, edit content and ask validation for update
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("content:edit-title", args=[content_draft.pk]),
            {"title": content_draft.title + "2"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": content_draft.pk, "slug": content_draft.slug}),
            {"text": text_validation, "version": content_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # ensure the validation is effective
        self.assertEqual(Validation.objects.count(), 2)
        self.assertIsNotNone(Validation.objects.last().date_reserve)  # issue #3432

    def test_beta_article_closed_when_published(self):
        """Test that the beta of an article is locked when the content is published"""

        text_validation = "Valide moi ce truc !"
        text_publication = "Validation faite !"

        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user_author)
        article.save()
        article_draft = article.load_version()

        # login with author:
        self.client.force_login(self.user_author)

        # set beta
        result = self.client.post(
            reverse("content:set-beta", kwargs={"pk": article.pk, "slug": article.slug}),
            {"version": article_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": article.pk, "slug": article.slug}),
            {"text": text_validation, "version": article_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.client.logout()
        # login with staff
        self.client.force_login(self.user_staff)

        # reserve the article
        validation = Validation.objects.filter(content=article).last()
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # Check that the staff user doesn't have a notification for their reservation and their private topic is read.
        self.assertEqual(0, len(Notification.objects.get_unread_notifications_of(self.user_staff)))
        last_pm = PrivateTopic.objects.get_private_topics_of_user(self.user_staff.pk).last()
        self.assertFalse(is_privatetopic_unread(last_pm, self.user_staff))

        # publish the article
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        beta_topic = PublishableContent.objects.get(pk=article.pk).beta_topic
        self.assertIsNotNone(beta_topic)
        self.assertTrue(beta_topic.is_locked)
        last_message = beta_topic.last_message
        self.assertIsNotNone(last_message)

        # login with author to ensure that the beta is not closed if it was already closed (at a second validation).
        self.client.force_login(self.user_author)

        # ask validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": article.pk, "slug": article.slug}),
            {"text": text_validation, "version": article_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff
        self.client.force_login(self.user_staff)

        # reserve the article
        validation = Validation.objects.filter(content=article).last()
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # publish the article
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        beta_topic = PublishableContent.objects.get(pk=article.pk).beta_topic
        self.assertIsNotNone(beta_topic)
        self.assertTrue(beta_topic.is_locked)
        self.assertEqual(beta_topic.last_message, last_message)

    def test_obsolete(self):
        # check that this function is only available for staff
        self.client.force_login(self.user_author)
        result = self.client.post(reverse("validation:mark-obsolete", kwargs={"pk": self.tuto.pk}), follow=False)
        self.assertEqual(result.status_code, 403)
        # login as staff
        self.client.force_login(self.user_staff)
        # check that when the content is not marked as obsolete, the alert is not shown
        result = self.client.get(self.tuto.get_absolute_url_online(), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertNotContains(result, _("Ce contenu est obsolète."))
        # now, let's mark the tutoriel as obsolete
        result = self.client.post(reverse("validation:mark-obsolete", kwargs={"pk": self.tuto.pk}), follow=False)
        self.assertEqual(result.status_code, 302)
        # check that the alert is shown
        result = self.client.get(self.tuto.get_absolute_url_online(), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, _("Ce contenu est obsolète."))
        # and on a chapter
        result = self.client.get(self.chapter1.get_absolute_url_online(), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, _("Ce contenu est obsolète."))
        # finally, check that this alert can be hidden
        result = self.client.post(reverse("validation:mark-obsolete", kwargs={"pk": self.tuto.pk}), follow=False)
        self.assertEqual(result.status_code, 302)
        result = self.client.get(self.tuto.get_absolute_url_online(), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertNotContains(result, _("Ce contenu est obsolète."))

    def test_list_publications(self):
        """Test the behavior of the publication list"""

        category_1 = CategoryFactory()
        category_2 = CategoryFactory()
        subcategory_1 = SubCategoryFactory(category=category_1)
        subcategory_2 = SubCategoryFactory(category=category_1)
        subcategory_3 = SubCategoryFactory(category=category_2)
        subcategory_4 = SubCategoryFactory(category=category_2)
        tag_1 = Tag(title="random")
        tag_1.save()

        tuto_p_1 = PublishedContentFactory(author_list=[self.user_author])
        tuto_p_2 = PublishedContentFactory(author_list=[self.user_author])
        tuto_p_3 = PublishedContentFactory(author_list=[self.user_author])

        article_p_1 = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")

        tuto_p_1.subcategory.add(subcategory_1)
        tuto_p_1.subcategory.add(subcategory_2)
        tuto_p_1.save()

        tuto_p_2.subcategory.add(subcategory_1)
        tuto_p_2.subcategory.add(subcategory_2)
        tuto_p_2.save()

        tuto_p_3.subcategory.add(subcategory_3)
        tuto_p_3.save()

        article_p_1.subcategory.add(subcategory_4)
        article_p_1.tags.add(tag_1)
        article_p_1.save()

        tuto_1 = PublishedContent.objects.get(content=tuto_p_1.pk)
        tuto_2 = PublishedContent.objects.get(content=tuto_p_2.pk)
        tuto_3 = PublishedContent.objects.get(content=tuto_p_3.pk)
        article_1 = PublishedContent.objects.get(content=article_p_1.pk)

        self.assertEqual(PublishableContent.objects.filter(type="ARTICLE").count(), 1)
        self.assertEqual(PublishableContent.objects.filter(type="TUTORIAL").count(), 4)

        # 1. Publication list
        result = self.client.get(reverse("publication:list"))
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 1)
        self.assertEqual(len(result.context["last_tutorials"]), 4)

        # 2. Category page
        result = self.client.get(reverse("publication:category", kwargs={"slug": category_1.slug}))
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 0)
        self.assertEqual(len(result.context["last_tutorials"]), 2)

        pks = [x.pk for x in result.context["last_tutorials"]]
        self.assertIn(tuto_1.pk, pks)
        self.assertIn(tuto_2.pk, pks)

        result = self.client.get(reverse("publication:category", kwargs={"slug": category_2.slug}))
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 1)
        self.assertEqual(len(result.context["last_tutorials"]), 1)

        pks = [x.pk for x in result.context["last_tutorials"]]
        self.assertIn(tuto_3.pk, pks)

        pks = [x.pk for x in result.context["last_articles"]]
        self.assertIn(article_1.pk, pks)

        # 3. Subcategory page
        result = self.client.get(
            reverse("publication:subcategory", kwargs={"slug_category": category_1.slug, "slug": subcategory_1.slug})
        )

        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 0)
        self.assertEqual(len(result.context["last_tutorials"]), 2)

        pks = [x.pk for x in result.context["last_tutorials"]]
        self.assertIn(tuto_1.pk, pks)
        self.assertIn(tuto_2.pk, pks)

        result = self.client.get(
            reverse("publication:subcategory", kwargs={"slug_category": category_1.slug, "slug": subcategory_2.slug})
        )

        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 0)
        self.assertEqual(len(result.context["last_tutorials"]), 2)

        pks = [x.pk for x in result.context["last_tutorials"]]
        self.assertIn(tuto_1.pk, pks)
        self.assertIn(tuto_2.pk, pks)

        result = self.client.get(
            reverse("publication:subcategory", kwargs={"slug_category": category_2.slug, "slug": subcategory_3.slug})
        )

        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 0)
        self.assertEqual(len(result.context["last_tutorials"]), 1)

        pks = [x.pk for x in result.context["last_tutorials"]]
        self.assertIn(tuto_3.pk, pks)

        result = self.client.get(
            reverse("publication:subcategory", kwargs={"slug_category": category_2.slug, "slug": subcategory_4.slug})
        )

        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["last_articles"]), 1)
        self.assertEqual(len(result.context["last_tutorials"]), 0)

        pks = [x.pk for x in result.context["last_articles"]]
        self.assertIn(article_1.pk, pks)

        # 4. Final page and filters
        result = self.client.get(reverse("publication:list") + f"?category={category_1.slug}")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 2)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(tuto_1.pk, pks)
        self.assertIn(tuto_2.pk, pks)

        # filter by category and type
        result = self.client.get(reverse("publication:list") + f"?category={category_2.slug}")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 2)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(tuto_3.pk, pks)
        self.assertIn(article_1.pk, pks)

        result = self.client.get(reverse("publication:list") + f"?category={category_2.slug}" + "&type=article")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 1)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(article_1.pk, pks)

        result = self.client.get(reverse("publication:list") + f"?category={category_2.slug}" + "&type=tutorial")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 1)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(tuto_3.pk, pks)

        # filter by subcategory
        result = self.client.get(reverse("publication:list") + f"?subcategory={subcategory_1.slug}")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 2)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(tuto_1.pk, pks)
        self.assertIn(tuto_2.pk, pks)

        # filter by subcategory and type
        result = self.client.get(reverse("publication:list") + f"?subcategory={subcategory_3.slug}")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 1)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(tuto_3.pk, pks)

        result = self.client.get(reverse("publication:list") + f"?subcategory={subcategory_3.slug}" + "&type=article")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context["filtered_contents"]), 0)

        result = self.client.get(reverse("publication:list") + f"?subcategory={subcategory_3.slug}" + "&type=tutorial")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 1)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(tuto_3.pk, pks)

        # filter by tag
        result = self.client.get(reverse("publication:list") + f"?tag={tag_1.slug}" + "&type=article")
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(result.context["filtered_contents"]), 1)
        pks = [x.pk for x in result.context["filtered_contents"]]
        self.assertIn(article_1.pk, pks)

        # 5. Everything else results in 404
        wrong_urls = [
            # not existing (sub)categories, types or tags with slug "xxx"
            reverse("publication:list") + "?category=xxx",
            reverse("publication:list") + "?subcategory=xxx",
            reverse("publication:list") + "?type=xxx",
            reverse("publication:list") + "?tag=xxx",
            reverse("publication:category", kwargs={"slug": "xxx"}),
            reverse("publication:subcategory", kwargs={"slug_category": category_2.slug, "slug": "xxx"}),
            # subcategory_1 does not belong to category_2:
            reverse("publication:subcategory", kwargs={"slug_category": category_2.slug, "slug": subcategory_1.slug}),
        ]

        for url in wrong_urls:
            self.assertEqual(self.client.get(url).status_code, 404, msg=url)

    def test_article_previous_link(self):
        """Test the behaviour of the article previous link."""

        article_1 = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_2 = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_3 = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_1.save()
        article_2.save()
        article_3.save()

        result = self.client.get(reverse("article:view", kwargs={"pk": article_3.pk, "slug": article_3.slug}))

        self.assertEqual(result.context["previous_content"].pk, article_2.public_version.pk)

    def test_opinion_link_is_not_related_to_the_author(self):
        """
        Test that the next and previous link in the opinion page take all the opinions
        into account and not only the ones of the author.
        """

        opinion_not_picked = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        opinion_not_picked.save()

        user_1_opinion_1 = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        user_1_opinion_1.sha_picked = user_1_opinion_1.sha_public
        user_1_opinion_1.save()

        opinion_not_picked = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        opinion_not_picked.save()

        user_2_opinion_1 = PublishedContentFactory(author_list=[self.user_guest], type="OPINION")
        user_2_opinion_1.sha_picked = user_2_opinion_1.sha_public
        user_2_opinion_1.save()

        opinion_not_picked = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        opinion_not_picked.save()

        user_1_opinion_2 = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        user_1_opinion_2.sha_picked = user_1_opinion_2.sha_public
        user_1_opinion_2.save()

        opinion_not_picked = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        opinion_not_picked.save()

        PickListOperation.objects.create(
            content=user_1_opinion_1,
            operation="PICK",
            staff_user=self.user_staff,
            operation_date=datetime.datetime.now(),
            version=user_1_opinion_1.sha_public,
        )
        PickListOperation.objects.create(
            content=user_2_opinion_1,
            operation="PICK",
            staff_user=self.user_staff,
            operation_date=datetime.datetime.now(),
            version=user_2_opinion_1.sha_public,
        )
        PickListOperation.objects.create(
            content=user_1_opinion_2,
            operation="PICK",
            staff_user=self.user_staff,
            operation_date=datetime.datetime.now(),
            version=user_1_opinion_2.sha_public,
        )

        result = self.client.get(
            reverse("opinion:view", kwargs={"pk": user_1_opinion_2.pk, "slug": user_1_opinion_2.slug})
        )

        self.assertEqual(result.context["previous_content"].pk, user_2_opinion_1.public_version.pk)

        result = self.client.get(
            reverse("opinion:view", kwargs={"pk": user_2_opinion_1.pk, "slug": user_2_opinion_1.slug})
        )

        self.assertEqual(result.context["previous_content"].pk, user_1_opinion_1.public_version.pk)
        self.assertEqual(result.context["next_content"].pk, user_1_opinion_2.public_version.pk)

    def test_author_update(self):
        """Check that the author list of a content is updated when this content is updated."""

        text_validation = "Valide moi ce truc, please !"
        text_publication = "Validation faite !"

        tutorial = PublishedContentFactory(
            type="TUTORIAL", author_list=[self.user_author, self.user_guest, self.user_staff]
        )

        # Remove author to check if it's correct after major update
        tutorial.authors.remove(self.user_guest)
        tutorial.save()
        tutorial_draft = tutorial.load_version()

        # ask validation
        self.client.force_login(self.user_staff)
        self.client.post(
            reverse("validation:ask", kwargs={"pk": tutorial.pk, "slug": tutorial.slug}),
            {"text": text_validation, "version": tutorial_draft.current_version},
            follow=False,
        )

        # major update
        validation = Validation.objects.filter(content=tutorial).last()
        self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": True},
            follow=False,
        )
        self.assertEqual(tutorial.public_version.authors.count(), 2)

        # Remove author to check if it's correct after minor update
        tutorial.authors.remove(self.user_author)
        tutorial.save()
        tutorial_draft = tutorial.load_version()

        # ask validation
        self.client.force_login(self.user_staff)
        self.client.post(
            reverse("validation:ask", kwargs={"pk": tutorial.pk, "slug": tutorial.slug}),
            {"text": text_validation, "version": tutorial_draft.current_version},
            follow=False,
        )

        # minor update
        validation = Validation.objects.filter(content=tutorial).last()
        self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_publication, "is_major": False},
            follow=False,
        )

        self.assertEqual(tutorial.public_version.authors.count(), 1)

    def check_images_socials(self, result, pattern_link_image, title, description):
        start_reg = r"<meta(\s+)(\S+)"

        for meta in ["twitter:image", "og:image:url"]:
            self.assertRegex(
                result.content.decode("utf-8"),
                start_reg + meta + r'(\S+)(\s+)content="http://(\S+)/' + pattern_link_image + r'(\S+)"',
            )
        for meta in ["og:image:secure_url"]:
            self.assertRegex(
                result.content.decode("utf-8"),
                start_reg + meta + r'(\S+)(\s+)content="https://(\S+)/' + pattern_link_image + r'(\S+)"',
            )
        for meta in ["twitter:description"]:
            self.assertRegex(result.content.decode("utf-8"), start_reg + meta + r'(\S+)(\s+)content="' + description)
        for meta in ["twitter:title", "og:title"]:
            self.assertRegex(result.content.decode("utf-8"), start_reg + meta + r'(\S+)(\s+)content="' + title)

    def test_social_cards_without_image(self):
        """
        Check that all cards are produce for social network X
        """
        # test access for guest user (bot of social network for example)
        self.client.logout()

        # check tutorial cards
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}))
        self.assertEqual(result.status_code, 200)

        self.check_images_socials(result, "static/images/tutorial-illu", self.tuto.title, self.tuto.description)

        # check part cards
        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug, "container_slug": self.part1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)

        self.check_images_socials(result, "static/images/tutorial-illu", self.part1.title, self.tuto.description)

        # check chapter cards
        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": self.tuto.pk,
                    "slug": self.tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 200)

        self.check_images_socials(result, "static/images/tutorial-illu", self.chapter1.title, self.tuto.description)

    def test_social_cards_with_image(self):
        """Check that all cards are produced for socials network"""
        self.client.force_login(self.user_author)

        # Add image to public tutorial
        self.client.post(
            reverse("content:edit-thumbnail", args=[self.tuto.pk]),
            {"image": (settings.BASE_DIR / "fixtures" / "logo.png").open("rb")},
            follow=True,
        )

        # Test as a guest (bot of social network for example)
        self.client.logout()

        # Check tutorial cards
        result = self.client.get(reverse("tutorial:view", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}))
        self.assertEqual(result.status_code, 200)
        self.check_images_socials(result, "media/galleries/", self.tuto.title, self.tuto.description)

        # Check part cards
        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug, "container_slug": self.part1.slug},
            )
        )
        self.assertEqual(result.status_code, 200)
        self.check_images_socials(result, "media/galleries/", self.part1.title, self.tuto.description)

        # Check chapter cards
        result = self.client.get(
            reverse(
                "tutorial:view-container",
                kwargs={
                    "pk": self.tuto.pk,
                    "slug": self.tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            )
        )
        self.assertEqual(result.status_code, 200)
        self.check_images_socials(result, "media/galleries/", self.chapter1.title, self.tuto.description)

    def test_add_help_tuto(self):
        self.client.force_login(self.user_author)
        tutorial = PublishableContentFactory(author_list=[self.user_author])
        help_wanted = HelpWritingFactory()
        resp = self.client.post(
            reverse("content:helps-change", args=[tutorial.pk]), {"activated": True, "help_wanted": help_wanted.title}
        )
        self.assertEqual(302, resp.status_code)
        self.assertEqual(1, PublishableContent.objects.filter(pk=tutorial.pk).first().helps.count())

    def test_add_help_opinion(self):
        self.client.force_login(self.user_author)
        tutorial = PublishableContentFactory(author_list=[self.user_author], type="OPINION")
        help_wanted = HelpWritingFactory()
        resp = self.client.post(
            reverse("content:helps-change", args=[tutorial.pk]), {"activated": True, "help_wanted": help_wanted.title}
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual(0, PublishableContent.objects.filter(pk=tutorial.pk).first().helps.count())

    def test_save_no_redirect(self):
        self.client.force_login(self.user_author)
        tutorial = PublishableContentFactory(author_list=[self.user_author])
        extract = ExtractFactory(db_object=tutorial, container=tutorial.load_version())
        tutorial = PublishableContent.objects.get(pk=tutorial.pk)
        resp = self.client.post(
            reverse("content:edit-extract", args=[tutorial.pk, tutorial.slug, extract.slug]),
            {
                "last_hash": extract.compute_hash(),
                "text": "a brand new text",
                "title": extract.title,
                "msg_commit": "a commit message",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            follow=False,
        )
        # no redirect
        self.assertEqual(200, resp.status_code)
        result = loads(resp.content.decode("utf-8"))
        self.assertEqual("ok", result.get("result", None))
        self.assertEqual(extract.compute_hash(), result.get("last_hash", None))

    def test_remove_unpublished_opinion_with_alerted_comments(self):
        """Test the page showing alerts with an alerted comment on a removed opinion"""

        alert_page_url = reverse("pages-alerts")

        # 1. Publish opinion
        opinion = PublishedContentFactory(type="OPINION", author_list=[self.user_author])

        # 2. Comment the opinion
        random_user = ProfileFactory().user
        comment = ContentReactionFactory(related_content=opinion, author=random_user)

        # 3. Create an alert for the comment
        self.client.force_login(self.user_staff)
        result = self.client.post(
            reverse("content:alert-reaction", args=[comment.pk]),
            {"signal_text": "No. Try not. Do... or do not. There is no try."},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # 4. Display the page listing alerts
        resp = self.client.get(alert_page_url)
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, comment.get_absolute_url())  # We have a link to the alerted comment
        self.assertEqual(len(resp.context["alerts"]), 1)
        self.assertEqual(len(resp.context["solved"]), 0)

        # 5. Unpublish the opinion
        result = self.client.post(
            reverse("validation:ignore-opinion", kwargs={"pk": opinion.pk, "slug": opinion.slug}),
            {
                "operation": "REMOVE_PUB",
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # 6. Display the page listing alerts
        resp = self.client.get(alert_page_url)
        self.assertEqual(200, resp.status_code)
        self.assertNotContains(resp, 'href="?page=1#p')  # We don't have wrong links
        self.assertEqual(len(resp.context["alerts"]), 0)
        self.assertEqual(len(resp.context["solved"]), 1)

        # 7. Remove the opinion
        self.client.force_login(self.user_author)
        result = self.client.post(reverse("content:delete", args=[opinion.pk, opinion.slug]), follow=False)
        self.assertEqual(result.status_code, 302)

        # 8. Display the page listing alerts
        self.client.force_login(self.user_staff)
        resp = self.client.get(alert_page_url)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(len(resp.context["alerts"]), 0)
        self.assertEqual(len(resp.context["solved"]), 0)
