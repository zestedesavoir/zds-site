import datetime
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import HttpResponseNotAllowed
from django.test import TestCase
from django.urls import reverse

from zds import json_handler
from zds.forum.models import Post, Topic, TopicRead
from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.gallery.models import Gallery, Image, UserGallery
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.mp.models import PrivatePost, PrivateTopic
from zds.notification.models import ContentReactionAnswerSubscription, NewPublicationSubscription, Notification
from zds.tutorialv2.models.database import PublishableContent, PublishedContent, Validation
from zds.tutorialv2.models.help_requests import HelpWriting
from zds.tutorialv2.publication_utils import (
    Publicator,
    PublicatorRegistry,
    ZMarkdownEpubPublicator,
    ZMarkdownRebberLatexPublicator,
)
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    BetaContentFactory,
    ContainerFactory,
    ExtractFactory,
    HelpWritingFactory,
    PublishableContentFactory,
    PublishedContentFactory,
    tricky_text_content,
)
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


@override_for_contents()
class ContentTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        self.overridden_zds_app["member"]["bot_account"] = self.mas.username

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode="W")
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
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
        bot = Group(name=self.overridden_zds_app["member"]["bot_group"])
        bot.save()
        self.external = UserFactory(username=self.overridden_zds_app["member"]["external_account"], password="anything")
        self.old_registry = {key: value for key, value in PublicatorRegistry.get_all_registered()}

        class TestPdfPublicator(Publicator):
            def publish(self, md_file_path, base_name, **kwargs):
                with Path(base_name + ".pdf").open("w") as f:
                    f.write("bla")

                shutil.copy2(str(Path(base_name + ".pdf")), str(Path(md_file_path.replace("__building", "")).parent))

        PublicatorRegistry.registry["pdf"] = TestPdfPublicator()
        PublicatorRegistry.registry["printable-pdf"] = TestPdfPublicator()

    def test_ensure_access(self):
        """General access test for author, user, guest and staff"""

        # login with author
        self.client.force_login(self.user_author)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for author (get 200, for content, part, chapter)
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            reverse(
                "content:edit-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            result.content.decode("utf-8"),
        )
        result = self.client.get(
            reverse(
                "content:view-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        self.client.logout()

        # check access for public (get 302, for content, part, chapter)
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse(
                "content:view-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with guest
        self.client.force_login(self.user_guest)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for guest (get 403 for content, part and chapter, since he is not part of the authors)
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse(
                "content:view-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        # login with staff
        self.client.force_login(self.user_staff)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for staff (get 200 for content, part and chapter)
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

    def test_create_tutorial(self):
        """Test the creation of a new content."""
        self.client.force_login(self.user_author)

        title = "un titre"
        result = self.client.post(
            reverse("content:create-content", kwargs={"created_content_type": "TUTORIAL"}),
            {"title": title, "type": "TUTORIAL"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        self.assertEqual(Gallery.objects.filter(pk=tuto.gallery.pk).count(), 1)
        self.assertEqual(UserGallery.objects.filter(gallery__pk=tuto.gallery.pk).count(), tuto.authors.count())

    def test_basic_tutorial_workflow(self):
        """General test on the basic workflow of a tutorial: edition, deletion for the author"""
        self.client.force_login(self.user_author)

        # create tutorial
        intro = "une intro"
        conclusion = "une conclusion"
        description = "une description"
        title = "un titre"
        random = "un truc à la rien à voir"
        random_with_md = "un text contenant du **markdown** ."

        tuto = PublishableContentFactory(type="TUTORIAL")
        tuto.authors.add(self.user_author)
        pk = tuto.pk
        slug = tuto.slug

        # preview container
        result = self.client.post(
            reverse("content:create-container", args=[pk, slug]),
            {"title": title, "text": random_with_md, "preview": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        result_string = "".join(a.decode() for a in result.streaming_content)
        self.assertIn("<strong>markdown</strong>", result_string, "We need the container to be properly formatted")

        # create container:
        result = self.client.post(
            reverse("content:create-container", args=[pk, slug]),
            {"title": title, "introduction": intro, "conclusion": conclusion},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()

        self.assertEqual(len(versioned.children), 1)  # ok, the container is created
        container = versioned.children[0]
        self.assertEqual(container.title, title)
        self.assertEqual(container.get_introduction(), intro)
        self.assertEqual(container.get_conclusion(), conclusion)

        # access container:
        result = self.client.get(
            reverse("content:view-container", kwargs={"pk": pk, "slug": slug, "container_slug": container.slug}),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # edit container:
        result = self.client.post(
            reverse("content:edit-container", kwargs={"pk": pk, "slug": slug, "container_slug": container.slug}),
            {"title": random, "introduction": random, "conclusion": random, "last_hash": container.compute_hash()},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        container = versioned.children[0]

        # preview
        result = self.client.post(
            reverse("content:edit-container", kwargs={"pk": pk, "slug": slug, "container_slug": container.slug}),
            {"title": random, "text": random_with_md, "last_hash": container.compute_hash(), "preview": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(result.status_code, 200)

        result_string = "".join(a.decode() for a in result.streaming_content)
        self.assertIn("<strong>markdown</strong>", result_string, "We need the container to be properly formatted")

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        container = versioned.children[0]
        self.assertEqual(container.title, random)
        self.assertEqual(container.get_introduction(), random)
        self.assertEqual(container.get_conclusion(), random)

        # add a subcontainer
        result = self.client.post(
            reverse("content:create-container", kwargs={"pk": pk, "slug": slug, "container_slug": container.slug}),
            {"title": title, "introduction": intro, "conclusion": conclusion},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children), 1)  # the subcontainer is created
        subcontainer = versioned.children[0].children[0]
        self.assertEqual(subcontainer.title, title)
        self.assertEqual(subcontainer.get_introduction(), intro)
        self.assertEqual(subcontainer.get_conclusion(), conclusion)

        # access the subcontainer
        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # edit subcontainer:
        result = self.client.post(
            reverse(
                "content:edit-container",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                },
            ),
            {"title": random, "introduction": random, "conclusion": random, "last_hash": subcontainer.compute_hash()},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        subcontainer = versioned.children[0].children[0]

        result = self.client.post(
            reverse(
                "content:edit-container",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                },
            ),
            {"title": random, "text": random_with_md, "last_hash": subcontainer.compute_hash(), "preview": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        result_string = "".join(a.decode() for a in result.streaming_content)
        self.assertIn("<strong>markdown</strong>", result_string, "We need the container to be properly formatted")

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        subcontainer = versioned.children[0].children[0]
        self.assertEqual(subcontainer.title, random)
        self.assertEqual(subcontainer.get_introduction(), random)
        self.assertEqual(subcontainer.get_conclusion(), random)

        # add extract to subcontainer:
        result = self.client.post(
            reverse(
                "content:create-extract",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                },
            ),
            {"title": title, "text": description},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        result = self.client.post(
            reverse(
                "content:create-extract",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                },
            ),
            {"title": title, "text": random_with_md, "preview": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        result_string = "".join(a.decode() for a in result.streaming_content)
        self.assertIn("<strong>markdown</strong>", result_string, "We need the extract to be properly formatted")

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children[0].children), 1)  # the extract is created
        extract = versioned.children[0].children[0].children[0]
        self.assertEqual(extract.title, title)
        self.assertEqual(extract.get_text(), description)

        # access the subcontainer again (with the extract)
        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # edit extract:
        old_slug_extract = extract.slug
        result = self.client.post(
            reverse(
                "content:edit-extract",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                    "extract_slug": extract.slug,
                },
            ),
            {"title": random, "text": random, "last_hash": extract.compute_hash()},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        extract = versioned.children[0].children[0].children[0]
        self.assertEqual(extract.title, random)
        self.assertEqual(extract.get_text(), random)
        self.assertNotEqual(old_slug_extract, extract.slug)

        # then, delete extract:
        result = self.client.get(
            reverse(
                "content:delete",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                    "object_slug": extract.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 405)  # it is not working with get !

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children[0].children), 1)  # and the extract still exists

        result = self.client.post(
            reverse(
                "content:delete",
                kwargs={
                    "pk": pk,
                    "slug": slug,
                    "parent_container_slug": container.slug,
                    "container_slug": subcontainer.slug,
                    "object_slug": extract.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children[0].children), 0)  # extract was deleted
        self.assertFalse(os.path.exists(extract.get_path()))  # and physically deleted as well

        # delete subcontainer:
        result = self.client.post(
            reverse(
                "content:delete",
                kwargs={"pk": pk, "slug": slug, "container_slug": container.slug, "object_slug": subcontainer.slug},
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children), 0)  # subcontainer was deleted
        self.assertFalse(os.path.exists(subcontainer.get_path()))

        # delete container:
        result = self.client.post(
            reverse("content:delete", kwargs={"pk": pk, "slug": slug, "object_slug": container.slug}), follow=False
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children), 0)  # container was deleted
        self.assertFalse(os.path.exists(container.get_path()))

        # and delete tutorial itself
        gallery = PublishableContent.objects.get(pk=pk).gallery
        result = self.client.post(reverse("content:delete", args=[pk, slug]), follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertFalse(os.path.isfile(versioned.get_path()))  # deletion get right ;)
        self.assertEqual(PublishableContent.objects.filter(pk=pk).count(), 0)  # deleted from database

        self.assertEqual(Gallery.objects.filter(pk=gallery.pk).count(), 0)  # deletion of the gallery

        # check beta behaviour on deletion
        beta_content = BetaContentFactory(author_list=[self.user_author], forum=self.beta_forum)
        beta_topic = beta_content.beta_topic
        result = self.client.post(reverse("content:delete", args=[beta_content.pk, beta_content.slug]), follow=True)
        self.assertEqual(result.status_code, 200)
        beta_topic = Topic.objects.get(pk=beta_topic.pk)
        self.assertTrue(beta_topic.is_locked)

    def test_history_navigation(self):
        """ensure that, if the title (and so the slug) of the content change, its content remain accessible"""
        # login with author
        self.client.force_login(self.user_author)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # edit tutorial:
        old_slug_tuto = tuto.slug
        version_1 = tuto.sha_draft  # 'version 1' is the one before any change

        result = self.client.post(
            reverse("content:edit-title", args=[tuto.pk]),
            {"title": "Pâques, c'est bientôt?"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        version_2 = tuto.sha_draft  # 'version 2' is the one with the different slug for the tutorial
        self.assertNotEqual(tuto.slug, old_slug_tuto)

        # check access using old slug and no version
        result = self.client.get(reverse("content:view", args=[tuto.pk, old_slug_tuto]), follow=False)
        self.assertEqual(result.status_code, 404)  # it is not possible, so get 404

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={"pk": tuto.pk, "slug": old_slug_tuto, "container_slug": self.part1.slug},
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": old_slug_tuto,
                    "parent_container_slug": self.part1.slug,
                    "container_slug": self.chapter1.slug,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        # check access with old slug and version
        route_parameters = {"pk": tuto.pk, "slug": old_slug_tuto, "version": version_1}
        url = reverse("content:view-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": old_slug_tuto,
            "container_slug": self.part1.slug,
            "version": version_1,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": old_slug_tuto,
            "parent_container_slug": self.part1.slug,
            "container_slug": self.chapter1.slug,
            "version": version_1,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # edit container:
        old_slug_part = self.part1.slug
        part1 = tuto.load_version().children[0]
        random = "Un, deux, trois, je vais dans les bois"
        result = self.client.post(
            reverse(
                "content:edit-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": self.part1.slug}
            ),
            {"title": random, "introduction": random, "conclusion": random, "last_hash": part1.compute_hash()},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        version_3 = tuto.sha_draft  # 'version 3' is the one with the modified part
        versioned = tuto.load_version()
        current_slug_part = versioned.children[0].slug

        # we can still access to the container using old slug !
        route_parameters = {"pk": tuto.pk, "slug": tuto.slug, "container_slug": old_slug_part, "version": version_2}
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": tuto.slug,
            "parent_container_slug": old_slug_part,
            "container_slug": self.chapter1.slug,
            "version": version_2,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # and even to it using version 1 and old tuto slug !!
        route_parameters = {"pk": tuto.pk, "slug": old_slug_tuto, "container_slug": old_slug_part, "version": version_1}
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": old_slug_tuto,
            "parent_container_slug": old_slug_part,
            "container_slug": self.chapter1.slug,
            "version": version_1,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # but you can also access it with the current slug (for retro-compatibility)

        route_parameters = {"pk": tuto.pk, "slug": tuto.slug, "container_slug": old_slug_part, "version": version_1}
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": tuto.slug,
            "parent_container_slug": old_slug_part,
            "container_slug": self.chapter1.slug,
            "version": version_1,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # delete part
        result = self.client.post(
            reverse("content:delete", kwargs={"pk": tuto.pk, "slug": tuto.slug, "object_slug": current_slug_part}),
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # we can still access to the part in version 3:
        route_parameters = {"pk": tuto.pk, "slug": tuto.slug, "container_slug": current_slug_part, "version": version_3}
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": tuto.slug,
            "parent_container_slug": current_slug_part,
            "container_slug": self.chapter1.slug,
            "version": version_3,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)

        # version 2:
        self.assertEqual(result.status_code, 200)
        route_parameters = {"pk": tuto.pk, "slug": tuto.slug, "container_slug": old_slug_part, "version": version_2}
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": tuto.slug,
            "parent_container_slug": old_slug_part,
            "container_slug": self.chapter1.slug,
            "version": version_2,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # version 1:
        route_parameters = {"pk": tuto.pk, "slug": old_slug_tuto, "container_slug": old_slug_part, "version": version_1}
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        route_parameters = {
            "pk": tuto.pk,
            "slug": old_slug_tuto,
            "parent_container_slug": old_slug_part,
            "container_slug": self.chapter1.slug,
            "version": version_1,
        }
        url = reverse("content:view-container-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

    def test_if_none(self):
        """ensure that everything is ok if `None` is set"""

        # login with author
        self.client.force_login(self.user_author)

        given_title = "Un titre que personne ne lira"
        some_text = "Tralalala !!"

        # let's cheat a little bit and use the 'manual way' to force `None`
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        versioned = tuto.load_version()
        sha = versioned.repo_add_container(given_title, None, None)
        new_container = versioned.children[-1]
        slug_new_container = versioned.children[-1].slug
        tuto.sha_draft = sha
        tuto.save()

        # test access
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": slug_new_container},
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:edit-container",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "container_slug": slug_new_container,
                },
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)  # access to edition page is ok

        # edit container:
        result = self.client.post(
            reverse(
                "content:edit-container",
                kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": slug_new_container},
            ),
            {
                "title": given_title,
                "introduction": some_text,
                "conclusion": some_text,
                "last_hash": new_container.compute_hash(),
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # test access
        result = self.client.get(reverse("content:view", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:view-container",
                kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": slug_new_container},
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                "content:edit-container",
                kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": slug_new_container},
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

    def test_export_content(self):
        """Test if content is exported well"""

        # login with author
        self.client.force_login(self.user_author)

        given_title = "Oh, le beau titre à lire !"
        some_text = "À lire à un moment ou un autre, Über utile"  # accentuated characters are important for the test

        # Create a tutorial and modify its introduction and conclusion
        result = self.client.post(
            reverse("content:create-content", kwargs={"created_content_type": "TUTORIAL"}),
            {"title": given_title, "type": "TUTORIAL"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        tuto_pk = tuto.pk
        tuto_slug = tuto.slug

        result = self.client.post(
            reverse("content:edit-introduction", args=[tuto.pk]),
            {"introduction": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        result = self.client.post(
            reverse("content:edit-conclusion", args=[tuto.pk]),
            {"conclusion": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # add a chapter
        result = self.client.post(
            reverse("content:create-container", args=[tuto_pk, tuto_slug]),
            {"title": given_title, "introduction": some_text, "conclusion": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        chapter = versioned.children[-1]

        # add extract to chapter
        result = self.client.post(
            reverse(
                "content:create-extract", kwargs={"pk": tuto_pk, "slug": tuto_slug, "container_slug": chapter.slug}
            ),
            {"title": given_title, "text": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(reverse("content:download-zip", args=[tuto_pk, tuto_slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), "__draft1.zip")
        f = open(draft_zip_path, "wb")
        f.write(result.content)
        f.close()

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        version_1 = versioned.current_version
        chapter = versioned.children[-1]
        extract = chapter.children[-1]
        archive = zipfile.ZipFile(draft_zip_path, "r")

        self.assertEqual(str(archive.read("manifest.json"), "utf-8"), versioned.get_json())

        found = True
        try:  # to the person who try to modify this test: I'm sorry, but the test does not say where the error is ;)
            archive.getinfo("introduction.md")
            archive.getinfo("conclusion.md")
            archive.getinfo(os.path.join(chapter.slug, "introduction.md"))
            archive.getinfo(os.path.join(chapter.slug, "conclusion.md"))
            archive.getinfo(os.path.join(chapter.slug, "conclusion.md"))
            archive.getinfo(extract.text)
        except KeyError:
            found = False

        self.assertTrue(found)

        where = [
            "introduction.md",
            "conclusion.md",
            os.path.join(chapter.slug, "introduction.md"),
            os.path.join(chapter.slug, "conclusion.md"),
            extract.text,
        ]

        for path in where:
            self.assertEqual(str(archive.read(path), "utf-8"), some_text)

        # add another extract to chapter
        different_title = "Un Über titre de la mort qui tue"  # one more times, mind accentuated characters !!
        different_text = "þ is a letter as well ? ¶ means paragraph, at least"
        result = self.client.post(
            reverse(
                "content:create-extract", kwargs={"pk": tuto_pk, "slug": tuto_slug, "container_slug": chapter.slug}
            ),
            {"title": different_title, "text": different_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(reverse("content:download-zip", args=[tuto_pk, tuto_slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path_2 = os.path.join(tempfile.gettempdir(), "__draft2.zip")
        f = open(draft_zip_path_2, "wb")
        f.write(result.content)
        f.close()

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        version_2 = versioned.current_version
        extract2 = versioned.children[-1].children[-1]
        self.assertNotEqual(extract.slug, extract2.slug)  # just ensure that we don't pick the same extract
        self.assertNotEqual(version_1, version_2)  # just to ensure that something happen, somehow

        archive = zipfile.ZipFile(draft_zip_path_2, "r")
        self.assertEqual(str(archive.read("manifest.json"), "utf-8"), versioned.get_json())

        found = True
        try:
            archive.getinfo(extract2.text)
        except KeyError:
            found = False
        self.assertTrue(found)

        self.assertEqual(different_text, str(archive.read(extract2.text), "utf-8"))

        # now, try versioned download:
        result = self.client.get(
            reverse("content:download-zip", args=[tuto_pk, tuto_slug]) + "?version=" + version_1, follow=False
        )
        self.assertEqual(result.status_code, 200)
        draft_zip_path_3 = os.path.join(tempfile.gettempdir(), "__draft3.zip")
        f = open(draft_zip_path_3, "wb")
        f.write(result.content)
        f.close()

        archive = zipfile.ZipFile(draft_zip_path_3, "r")

        found = True
        try:
            archive.getinfo(extract2.text)
        except KeyError:
            found = False
        self.assertFalse(found)  # if we download the old version, the new extract introduced in version 2 is not in

        found = True
        try:
            archive.getinfo(extract.text)
        except KeyError:
            found = False
        self.assertTrue(found)  # but the extract of version 1 is in !

        # clean up our mess
        os.remove(draft_zip_path)
        os.remove(draft_zip_path_2)
        os.remove(draft_zip_path_3)

    def test_import_create_content(self):
        """Test if the importation of a tuto is working"""

        # login with author
        self.client.force_login(self.user_author)

        given_title = "Une autre histoire captivante"
        some_text = "Il était une fois ... La suite."

        # create a tutorial
        result = self.client.post(
            reverse("content:create-content", kwargs={"created_content_type": "TUTORIAL"}),
            {"title": given_title, "type": "TUTORIAL"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        tuto_pk = tuto.pk
        tuto_slug = tuto.slug

        result = self.client.post(
            reverse("content:edit-introduction", args=[tuto.pk]),
            {"introduction": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        result = self.client.post(
            reverse("content:edit-conclusion", args=[tuto.pk]),
            {"conclusion": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # add a chapter
        result = self.client.post(
            reverse("content:create-container", args=[tuto_pk, tuto_slug]),
            {"title": given_title, "introduction": some_text, "conclusion": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        chapter = versioned.children[-1]

        # add extract to chapter
        result = self.client.post(
            reverse(
                "content:create-extract", kwargs={"pk": tuto_pk, "slug": tuto_slug, "container_slug": chapter.slug}
            ),
            {"title": given_title, "text": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(reverse("content:download-zip", args=[tuto_pk, tuto_slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), "__draft1.zip")
        f = open(draft_zip_path, "wb")
        f.write(result.content)
        f.close()

        first_version = PublishableContent.objects.get(pk=tuto_pk).load_version()

        # then, use the archive to create a new content (which will be a copy of this one)
        result = self.client.post(
            reverse("content:import-new"),
            {"archive": open(draft_zip_path, "rb"), "subcategory": self.subcategory.pk},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.count(), 3)
        new_tuto = PublishableContent.objects.last()
        self.assertNotEqual(new_tuto.pk, tuto_pk)  # those are two different content !

        # first, test if values are correctly set in DB
        self.assertEqual(new_tuto.title, tuto.title)
        self.assertEqual(new_tuto.description, tuto.description)
        self.assertEqual(new_tuto.licence, tuto.licence)
        self.assertEqual(new_tuto.type, tuto.type)

        self.assertNotEqual(new_tuto.slug, tuto_slug)  # slug should NEVER be the same !!

        # then, let's do the same for the versioned one
        versioned = new_tuto.load_version()

        self.assertEqual(first_version.title, versioned.title)
        self.assertEqual(first_version.description, versioned.description)
        self.assertEqual(first_version.licence, versioned.licence)
        self.assertEqual(first_version.type, versioned.type)

        # ensure the content
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(len(versioned.children), 1)

        new_chapter = versioned.children[-1]
        self.assertEqual(new_chapter.get_introduction(), some_text)
        self.assertEqual(new_chapter.get_conclusion(), some_text)
        self.assertEqual(len(new_chapter.children), 1)

        extract = new_chapter.children[-1]
        self.assertEqual(extract.get_text(), some_text)
        result = self.client.post(
            reverse("content:import-new"),
            {"archive": open(draft_zip_path, "rb"), "subcategory": self.subcategory.pk},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.count(), 4)
        second_tuto = PublishableContent.objects.last()
        self.assertNotEqual(new_tuto.pk, second_tuto.pk)  # those are two different content !
        first_versioned = new_tuto.load_version()
        second_versioned = second_tuto.load_version()
        self.assertNotEqual(second_versioned.slug, first_versioned.slug)
        # clean up
        os.remove(draft_zip_path)

    def test_import_in_existing_content(self):
        """Test if the importation of a content into another is working"""

        # login with author
        self.client.force_login(self.user_author)

        given_title = "Parce que le texte change à chaque fois"
        some_text = "Sinon, c'pas drôle"

        # create a tutorial
        result = self.client.post(
            reverse("content:create-content", kwargs={"created_content_type": "TUTORIAL"}),
            {"title": given_title, "type": "TUTORIAL"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        tuto_pk = tuto.pk
        tuto_slug = tuto.slug

        result = self.client.post(
            reverse("content:edit-introduction", args=[tuto.pk]),
            {"introduction": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        result = self.client.post(
            reverse("content:edit-conclusion", args=[tuto.pk]),
            {"conclusion": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # add a chapter
        result = self.client.post(
            reverse("content:create-container", args=[tuto_pk, tuto_slug]),
            {"title": given_title, "introduction": some_text, "conclusion": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        chapter = versioned.children[-1]

        # add extract to chapter
        result = self.client.post(
            reverse(
                "content:create-extract", kwargs={"pk": tuto_pk, "slug": tuto_slug, "container_slug": chapter.slug}
            ),
            {"title": given_title, "text": some_text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(reverse("content:download-zip", args=[tuto_pk, tuto_slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), "__draft1.zip")
        f = open(draft_zip_path, "wb")
        f.write(result.content)
        f.close()

        first_version = PublishableContent.objects.get(pk=tuto_pk).load_version()

        # then, use the archive to create a new content (which will be a copy of this one)
        result = self.client.post(
            reverse("content:import", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}),
            {"archive": open(draft_zip_path, "rb"), "subcategory": self.subcategory.pk},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.count(), 2)
        existing_tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertNotEqual(existing_tuto.pk, tuto_pk)  # those are two different content !

        # first, test if values are correctly set in DB
        self.assertEqual(existing_tuto.title, tuto.title)
        self.assertEqual(existing_tuto.description, tuto.description)
        self.assertEqual(existing_tuto.licence, tuto.licence)
        self.assertEqual(existing_tuto.type, tuto.type)

        self.assertNotEqual(existing_tuto.slug, tuto_slug)  # slug should NEVER be the same !!

        # then, let's do the same for the versioned one
        versioned = existing_tuto.load_version()

        self.assertEqual(first_version.title, versioned.title)
        self.assertEqual(first_version.description, versioned.description)
        self.assertEqual(first_version.licence, versioned.licence)
        self.assertEqual(first_version.type, versioned.type)

        # ensure the content
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(versioned.get_conclusion(), some_text)
        self.assertEqual(len(versioned.children), 1)

        new_chapter = versioned.children[-1]
        self.assertEqual(new_chapter.get_introduction(), some_text)
        self.assertEqual(new_chapter.get_conclusion(), some_text)
        self.assertEqual(len(new_chapter.children), 1)

        extract = new_chapter.children[-1]
        self.assertEqual(extract.get_text(), some_text)

        # clean up
        os.remove(draft_zip_path)

    def test_import_with_bad_title(self):
        """Tests an error case that happen when someone sends an archive that modify the content title
        with a string that cannont be properly slugified"""
        new_article = PublishableContentFactory(type="ARTICLE", title="extension", author_list=[self.user_author])
        self.client.force_login(self.user_author)
        archive_path = settings.BASE_DIR / "fixtures" / "tuto" / "BadArchive.zip"
        answer = self.client.post(
            reverse("content:import", args=[new_article.pk, new_article.slug]),
            {
                "archive": archive_path.open("rb"),
                "msg_commit": "let it go, let it goooooooo ! can't hold it back anymoooooore!",
            },
        )
        self.assertEqual(200, answer.status_code)
        msgs = answer.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

    def test_import_image_with_archive(self):
        """ensure that import archive work, and link are changed"""

        prefix = self.overridden_zds_app["content"]["import_image_prefix"]
        title = "OSEF ici du titre :p"
        text1 = f"![]({prefix}:image1.png) ![]({prefix}:dossier/image2.png)"
        text2 = f"![Piège](img3.png) ![Image qui existe pas]({prefix}:img3.png) ![](mauvais:img3.png)"

        # login with author
        self.client.force_login(self.user_author)

        # create an article
        article = PublishableContentFactory(type="ARTICLE", licence=self.licence)

        article.authors.add(self.user_author)
        UserGalleryFactory(gallery=article.gallery, user=self.user_author, mode="W")
        article.save()

        article_draft = article.load_version()

        article_draft.repo_add_extract(title, text1)
        version = article_draft.repo_add_extract(title, text2)

        article.sha_draft = version
        article.save()

        # check that there is no image in gallery
        self.assertEqual(Image.objects.filter(gallery=article.gallery).count(), 0)

        # download and store
        result = self.client.get(reverse("content:download-zip", args=[article.pk, article.slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), "__draft1.zip")
        f = open(draft_zip_path, "wb")
        f.write(result.content)
        f.close()

        # create the archive with images:
        image_zip_path = os.path.join(tempfile.gettempdir(), "__images.zip")
        zfile = zipfile.ZipFile(image_zip_path, "a")

        bytes = open("fixtures/noir_black.png", "rb").read()
        zfile.writestr("image1.png", bytes)
        zfile.writestr("dossier/image2.png", bytes)
        zfile.close()

        # then, use the archive to create a new content with images !
        result = self.client.post(
            reverse("content:import-new"),
            {
                "archive": open(draft_zip_path, "rb"),
                "image_archive": open(image_zip_path, "rb"),
                "subcategory": self.subcategory.pk,
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.count(), 3)  # import ok

        new_article = PublishableContent.objects.last()
        versioned = new_article.load_version()

        self.assertEqual(len(versioned.children), 2)
        self.assertEqual(Image.objects.filter(gallery=new_article.gallery).count(), 2)  # image import ok

        # check changes:
        self.assertNotEqual(versioned.children[0].get_text(), text1)
        self.assertEqual(versioned.children[1].get_text(), text2)

        # check links:
        text = versioned.children[0].get_text()
        for img in Image.objects.filter(gallery=new_article.gallery).all():
            self.assertTrue("![]({})".format(self.overridden_zds_app["site"]["url"] + img.physical.url) in text)

        # import into first article (that will only change the images)
        result = self.client.post(
            reverse("content:import", args=[article.pk, article.slug]),
            {
                "archive": open(draft_zip_path, "rb"),
                "image_archive": open(image_zip_path, "rb"),
                "subcategory": self.subcategory.pk,
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        new_version = PublishableContent.objects.get(pk=article.pk)
        versioned = new_version.load_version()

        self.assertEqual(len(versioned.children), 2)
        self.assertEqual(Image.objects.filter(gallery=new_version.gallery).count(), 2)  # image import ok

        # check changes:
        self.assertNotEqual(versioned.children[0].get_text(), text1)
        self.assertEqual(versioned.children[1].get_text(), text2)  # this one does not contains valid links

        # check links:
        text = versioned.children[0].get_text()
        for img in Image.objects.filter(gallery=new_version.gallery).all():
            self.assertTrue("![]({})".format(self.overridden_zds_app["site"]["url"] + img.physical.url) in text)

        # clean up
        os.remove(draft_zip_path)
        os.remove(image_zip_path)

    def test_import_ready_to_publish(self):
        """Test whether the 'ready_to_publish' info from the archive is correctly imported."""

        # General principle of this test:
        #   * create an archive by creating a content and exporting it
        #   * change the 'ready_to_publish' toggles on the content
        #   * import the archive and check whether we get back to the initial state (i.e. correct import)

        self.client.force_login(self.user_author)

        # Create a content with parts
        content = PublishableContentFactory(author_list=[self.user_author])
        versioned = content.load_version()
        part1 = ContainerFactory(db_object=content, parent=versioned)
        chapter1 = ContainerFactory(db_object=content, parent=part1)
        chapter1.ready_to_publish = False
        ContainerFactory(db_object=content, parent=part1)  # chapter 2
        part2 = ContainerFactory(db_object=content, parent=versioned)
        part2.ready_to_publish = False
        sha = versioned.repo_update(content.title, content.slug, "introduction", "conclusion")
        content.sha_draft = sha
        content.save()

        original_intro = versioned.get_introduction()
        original_conclu = versioned.get_conclusion()

        # Download archive of initial state for content
        result = self.client.get(reverse("content:download-zip", args=[content.pk, content.slug]), follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), "__draft1.zip")
        with open(draft_zip_path, "wb") as f:
            f.write(result.content)

        # Update readiness of part 2 and part1/chapter1
        # Failure to import this information defaults also to True, this is to make sure.
        versioned.children[0].children[0].ready_to_publish = True
        versioned.children[1].ready_to_publish = True
        sha = versioned.repo_update_top_container(content.title, content.slug, original_intro, original_conclu)
        content.sha_draft = sha
        content.save()

        # Import archive
        result = self.client.post(
            reverse("content:import", args=[content.pk, content.slug]),
            {"archive": open(draft_zip_path, "rb")},
        )
        self.assertEqual(result.status_code, 302)

        # Check override of previous modifications through the import
        content = PublishableContent.objects.get(pk=content.pk)  # reload from database
        versioned = content.load_version()
        self.assertTrue(versioned.children[0].ready_to_publish)
        self.assertTrue(versioned.children[0].children[1].ready_to_publish)
        self.assertFalse(versioned.children[0].children[0].ready_to_publish)
        self.assertFalse(versioned.children[1].ready_to_publish)

        self.assertEqual(original_intro, versioned.get_introduction())
        self.assertEqual(original_conclu, versioned.get_conclusion())

    def test_display_history(self):
        """Test DisplayHistory view"""

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # no public access
        self.client.logout()
        result = self.client.get(reverse("content:history", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 302)

        # login as guest and test the non-access
        self.client.logout()
        self.client.force_login(self.user_guest)
        result = self.client.get(reverse("content:history", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 403)

        # staff access
        self.client.logout()
        self.client.force_login(self.user_staff)
        result = self.client.get(reverse("content:history", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

        # login as author and test the access
        self.client.logout()
        self.client.force_login(self.user_author)
        result = self.client.get(reverse("content:history", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 200)

    def test_display_diff(self):
        """Test DisplayDiff view"""

        from git import objects

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        repo = tuto.load_version().repository
        commits = []
        for commit in objects.commit.Commit.iter_items(repo, "HEAD"):
            commits.append(commit)
        valid_sha1 = commits[0].hexsha
        valid_sha2 = commits[-1].hexsha
        invalid_sha = "a" * 40

        # login with author
        self.client.force_login(self.user_author)

        # check 404 if missing parameters
        result = self.client.get(
            reverse("content:diff", kwargs={"pk": tuto.pk, "slug": tuto.slug})
            + "?from="
            + valid_sha1,  # missing to parameter
            follow=False,
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            reverse("content:diff", kwargs={"pk": tuto.pk, "slug": tuto.slug})
            + "?to="
            + valid_sha1,  # missing from parameter
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        # check 404 if invalid SHA
        result = self.client.get(
            reverse("content:diff", kwargs={"pk": tuto.pk, "slug": tuto.slug})
            + "?from="
            + invalid_sha
            + "&to="
            + valid_sha2,  # from is not a valid SHA
            follow=False,
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            reverse("content:diff", kwargs={"pk": tuto.pk, "slug": tuto.slug})
            + "?from="
            + valid_sha1
            + "&to="
            + invalid_sha,  # to is not a valid SHA
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

        # check 200 with valid parameters
        result = self.client.get(
            reverse("content:diff", kwargs={"pk": tuto.pk, "slug": tuto.slug})
            + "?from="
            + valid_sha1
            + "&to="
            + valid_sha2,
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.get(
            reverse("content:diff", kwargs={"pk": tuto.pk, "slug": tuto.slug}) + "?from=HEAD&to=HEAD^", follow=False
        )
        self.assertEqual(result.status_code, 200)

    def test_validation_subscription(self):
        """test if the author suscribes to their own content"""

        text_validation = "Valide moi ce truc, s'il te plait"
        text_accept = "C'est cool, merci !"

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": self.tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        validation = Validation.objects.filter(content=tuto).last()
        self.assertIsNotNone(validation)

        self.assertEqual(validation.comment_authors, text_validation)
        self.assertEqual(validation.version, self.tuto_draft.current_version)
        self.assertEqual(validation.status, "PENDING")

        # validate with staff
        self.client.logout()
        self.client.force_login(self.user_staff)

        result = self.client.get(
            reverse("content:view-version", kwargs={"pk": tuto.pk, "slug": tuto.slug, "version": validation.version}),
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

        # reserve tuto:
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_accept, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "ACCEPT")
        self.assertEqual(validation.comment_validator, text_accept)

        self.assertIsNotNone(NewPublicationSubscription.objects.get_existing(self.user_author, self.user_author))
        self.assertTrue(
            ContentReactionAnswerSubscription.objects.get_existing(user=self.user_author, content_object=tuto).is_active
        )
        self.client.logout()

        # Re-ask a new validation
        self.client.force_login(self.user_author)

        # Update the title to spice things up
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()
        self.client.post(
            reverse("content:edit-title", args=[tuto.pk]),
            {"title": "new title so that everything explode"},
            follow=False,
        )

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": versioned.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 2)

        validation = Validation.objects.filter(content=tuto).last()
        self.assertIsNotNone(validation)

        self.assertEqual(validation.comment_authors, text_validation)
        self.assertEqual(validation.version, self.tuto_draft.current_version)
        self.assertEqual(validation.status, "PENDING")
        self.client.logout()

        # validate with staff
        self.client.force_login(self.user_staff)

        route_parameters = {"pk": tuto.pk, "slug": tuto.slug, "version": validation.version}
        url = reverse("content:view-version", kwargs=route_parameters)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)

        # reserve tuto:
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_accept, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Validation.objects.filter(content=tuto).count(), 2)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "ACCEPT")
        self.assertEqual(validation.comment_validator, text_accept)

        self.assertIsNotNone(NewPublicationSubscription.objects.get_existing(self.user_author, self.user_author))
        self.assertTrue(
            ContentReactionAnswerSubscription.objects.get_existing(user=self.user_author, content_object=tuto).is_active
        )
        self.client.logout()

    @patch("zds.tutorialv2.signals.validation_management")
    def test_validation_workflow(self, validation_management):
        """test the different case of validation"""

        text_validation = "Valide moi ce truc, s'il te plait"
        text_accept = "C'est cool, merci !"
        text_reject = "Je refuse ce contenu."

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": self.tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)
        self.assertEqual(validation_management.send.call_count, 1)
        self.assertEqual(validation_management.send.call_args[1]["action"], "request")

        validation = Validation.objects.filter(content=tuto).last()
        self.assertIsNotNone(validation)

        self.assertEqual(validation.comment_authors, text_validation)
        self.assertEqual(validation.version, self.tuto_draft.current_version)
        self.assertEqual(validation.status, "PENDING")

        # ensure that author (not staff) cannot access to the validation.
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 403)

        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_accept, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        self.assertEqual(Validation.objects.filter(content=tuto).last().status, "PENDING")

        # No access for unauthenticated users
        self.client.logout()
        url = reverse("content:view-version", kwargs={"pk": tuto.pk, "slug": tuto.slug, "version": validation.version})
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 302)  # public cannot access a tutorial in validation ...

        # No access for simple members
        self.client.force_login(self.user_guest)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 403)  # ... Same for guest ...

        # Access for staff
        self.client.force_login(self.user_staff)
        result = self.client.get(url, follow=False)
        self.assertEqual(result.status_code, 200)  # ... But staff can, obviously !

        # reserve tuto:
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(validation_management.send.call_count, 2)
        self.assertEqual(validation_management.send.call_args[1]["action"], "reserve")

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

        # unreserve
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(validation_management.send.call_count, 3)
        self.assertEqual(validation_management.send.call_args[1]["action"], "unreserve")

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING")
        self.assertEqual(validation.validator, None)

        # re-reserve
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

        # let's modify the tutorial and ask for a new validation :
        ExtractFactory(container=self.chapter1, db_object=tuto)
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.tuto_draft = tuto.load_version()

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": self.tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 2)

        self.assertEqual(Validation.objects.get(pk=validation.pk).status, "CANCEL")  # previous is canceled

        # ... Therefore, a new Validation object is created
        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)
        self.assertEqual(validation.version, self.tuto_draft.current_version)

        self.assertEqual(PublishableContent.objects.get(pk=tuto.pk).sha_validation, self.tuto_draft.current_version)

        self.assertEqual(PrivateTopic.objects.last().author, self.user_staff)  # admin has received a PM

        # ensure that author cannot publish himself
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_accept, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

        self.assertEqual(Validation.objects.filter(content=tuto).last().status, "PENDING_V")

        # reject it with staff !
        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:reject", kwargs={"pk": validation.pk}), {"text": ""}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")  # rejection is impossible without text
        private_topic_messages_count = PrivatePost.objects.filter(
            privatetopic__pk=validation.content.validation_private_message.pk
        ).count()
        result = self.client.post(
            reverse("validation:reject", kwargs={"pk": validation.pk}), {"text": text_reject}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "REJECT")
        self.assertEqual(validation.comment_validator, text_reject)
        self.assertEqual(validation_management.send.call_count, 6)
        self.assertEqual(validation_management.send.call_args[1]["action"], "reject")

        self.assertIsNone(PublishableContent.objects.get(pk=tuto.pk).sha_validation)
        new_mp_message_nb = PrivatePost.objects.filter(
            privatetopic__pk=validation.content.validation_private_message.pk
        ).count()
        self.assertEqual(private_topic_messages_count + 1, new_mp_message_nb)  # author has received a PM

        # re-ask for validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": self.tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.filter(content=tuto).count(), 3)

        # a new object is created !
        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "PENDING")
        self.assertEqual(validation.validator, None)
        self.assertEqual(validation.version, self.tuto_draft.current_version)

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)
        self.assertEqual(validation.version, self.tuto_draft.current_version)

        # accept
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}), {"text": "", "is_major": True}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")  # acceptation is not possible without text

        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": text_accept, "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Validation.objects.filter(content=tuto).count(), 3)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "ACCEPT")
        self.assertEqual(validation.comment_validator, text_accept)
        self.assertEqual(validation_management.send.call_count, 9)
        self.assertEqual(validation_management.send.call_args[1]["action"], "accept")

        self.assertIsNone(PublishableContent.objects.get(pk=tuto.pk).sha_validation)

        subscription = NewPublicationSubscription.objects.get_existing(
            user=self.user_author, content_object=self.user_author
        )
        # subscription must be deactivated.
        self.assertFalse(subscription.is_active)
        self.assertEqual(1, Notification.objects.filter(subscription=subscription, is_read=False).count())

        self.assertEqual(PublishedContent.objects.filter(content=tuto).count(), 1)
        published = PublishedContent.objects.filter(content=tuto).first()

        self.assertTrue(
            ContentReactionAnswerSubscription.objects.get_existing(user=self.user_author, content_object=tuto).is_active
        )

        self.assertEqual(published.content_public_slug, self.tuto_draft.slug)
        self.assertTrue(os.path.exists(published.get_prod_path()))
        # ... another test cover the file creation and so all, lets skip this part

        # ensure that author cannot revoke his own publication
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_reject, "version": published.sha_public},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)
        self.assertEqual(Validation.objects.filter(content=tuto).last().status, "ACCEPT")

        # revoke publication with staff
        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": "", "version": published.sha_public},
            follow=False,
        )

        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "ACCEPT")  # with no text, revocation is not possible

        result = self.client.post(
            reverse("validation:revoke", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_reject, "version": published.sha_public},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(validation_management.send.call_count, 10)
        self.assertEqual(validation_management.send.call_args[1]["action"], "revoke")

        self.assertEqual(Validation.objects.filter(content=tuto).count(), 3)

        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "PENDING")
        self.assertEqual(validation.version, tuto.sha_draft)

        self.assertIsNotNone(PublishableContent.objects.get(pk=tuto.pk).sha_validation)

        self.assertEqual(PublishedContent.objects.filter(content=tuto).count(), 0)
        self.assertFalse(os.path.exists(published.get_prod_path()))

        # so, reserve it
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

        # ... and cancel reservation with author
        text_cancel = "Nan, mais j'ai plus envie, en fait"
        nb_messages = PrivatePost.objects.filter(
            privatetopic__pk=validation.content.validation_private_message.pk
        ).count()
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("validation:cancel", kwargs={"pk": validation.pk}), {"text": text_cancel}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(validation_management.send.call_count, 12)
        self.assertEqual(validation_management.send.call_args[1]["action"], "cancel")

        self.assertEqual(Validation.objects.filter(content=tuto).count(), 3)

        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "CANCEL")  # the validation got canceled
        new_nb_message_mp = PrivatePost.objects.filter(
            privatetopic__pk=validation.content.validation_private_message.pk
        ).count()
        self.assertEqual(nb_messages + 1, new_nb_message_mp)
        self.assertEqual(PrivateTopic.objects.last().author, self.user_staff)  # admin has received another PM

    def test_auto_validation(self):
        """Test that a staff can validate himself"""

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        tuto.authors.add(self.user_staff)
        tuto.save()

        self.client.force_login(self.user_staff)
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": "Valide moi ce truc, s'il te plait", "version": self.tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        validation = Validation.objects.filter(content=tuto).last()
        self.assertIsNotNone(validation)

        self.assertTrue(self.user_staff in tuto.authors.all())
        self.assertEqual(0, PrivateTopic.objects.filter(author=self.user_staff, participants=self.user_staff).count())
        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertTrue(self.user_staff in tuto.authors.all())
        self.assertEqual(0, PrivateTopic.objects.filter(author=self.user_staff, participants=self.user_staff).count())

        validation = Validation.objects.filter(content=tuto).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

    def test_delete_while_validating(self):
        """this test ensure that the validator is warned if the content he is validing is removed"""

        text_validation = "Valide moi ce truc, s'il te plait"
        text_cancel = "Veux pas !"

        # let's create a medium-size tutorial
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": text_validation, "version": self.tuto_draft.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        validation = Validation.objects.filter(content=tuto).last()

        # login with staff and reserve
        self.client.logout()
        self.client.force_login(self.user_staff)

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, "PENDING_V")
        self.assertEqual(validation.validator, self.user_staff)

        # login with author, delete tuto
        self.client.logout()
        self.client.force_login(self.user_author)

        # does not work without a text
        result = self.client.post(reverse("content:delete", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 302)
        tuto_qs = PublishableContent.objects.filter(pk=tuto.pk)
        self.assertEqual(tuto_qs.count(), 1)  # not deleted
        self.assertEqual(Validation.objects.count(), 1)
        topic_pk = tuto_qs.first().validation_private_message.pk
        nb_of_messages = PrivatePost.objects.filter(privatetopic__pk=topic_pk).count()
        # now, will work
        result = self.client.post(
            reverse("content:delete", args=[tuto.pk, tuto.slug]), {"text": text_cancel}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.filter(pk=tuto.pk).count(), 0)  # BOOM, deleted !
        self.assertEqual(Validation.objects.count(), 0)  # no more validation objects
        self.assertEqual(PrivateTopic.objects.filter(author=self.user_staff).count(), 1)
        new_nb_of_message = PrivatePost.objects.filter(privatetopic__pk=topic_pk).count()
        self.assertEqual(nb_of_messages + 1, new_nb_of_message)

        self.assertEqual(PrivateTopic.objects.last().author, self.user_staff)  # admin has received a PM

    @patch("zds.tutorialv2.signals.jsfiddle_management")
    def test_js_fiddle_activation(self, jsfiddle_management):
        self.client.force_login(self.staff)
        result = self.client.post(
            reverse("content:activate-jsfiddle"), {"pk": self.tuto.pk, "js_support": "on"}, follow=True
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(jsfiddle_management.send.call_count, 1)
        updated = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertTrue(updated.js_support)
        result = self.client.post(
            reverse("content:activate-jsfiddle"),
            {"pk": self.tuto.pk},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)
        updated = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertFalse(updated.js_support)
        self.assertEqual(jsfiddle_management.send.call_count, 2)
        self.client.logout()

        self.client.force_login(self.user_author)
        result = self.client.post(reverse("content:activate-jsfiddle"), {"pk": self.tuto.pk, "js_support": True})
        self.assertEqual(result.status_code, 403)
        self.assertEqual(jsfiddle_management.send.call_count, 2)

    def test_validate_unexisting(self):
        self.client.force_login(self.user_author)
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}),
            {"text": "blaaaaa", "version": "unexistingversion"},
            follow=False,
        )
        self.assertEqual(Validation.objects.filter(content__pk=self.tuto.pk).count(), 0)
        self.assertEqual(result.status_code, 404)

    def test_help_to_perfect_tuto(self):
        """This test aim to unit test the 'help me to write my tutorial' interface.
        It is testing if the back-end is always sending back good datas"""

        # create some helps:
        num_of_helps = 5  # note: should be at least "2" for this test to be performed
        for i in range(num_of_helps):
            a = HelpWritingFactory()
            a.save()

        helps = HelpWriting.objects.all()

        # currently the tutorial is published with no beta, so back-end should return 0 tutorial
        response = self.client.get(reverse("content:helps"), follow=False)

        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 0)

        # then active the beta on tutorial :
        # first, login with author :
        self.client.force_login(self.user_author)

        sha_draft = PublishableContent.objects.get(pk=self.tuto.pk).sha_draft
        response = self.client.post(
            reverse("content:set-beta", kwargs={"pk": self.tuto.pk, "slug": self.tuto.slug}),
            {"version": sha_draft},
            follow=False,
        )
        self.assertEqual(302, response.status_code)
        sha_beta = PublishableContent.objects.get(pk=self.tuto.pk).sha_beta
        self.assertEqual(sha_draft, sha_beta)

        response = self.client.get(reverse("content:helps"), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 1)

        # However if we ask with a filter we will still get 0 !
        for helping in helps:
            response = self.client.get(reverse("content:helps") + f"?need={helping.slug}", follow=False)
            self.assertEqual(200, response.status_code)
            contents = response.context["contents"]
            self.assertEqual(len(contents), 0)

        # now tutorial is positive for every options
        # if we ask for any help we should get a positive answer for every filter !
        self.tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        for helping in helps:
            self.tuto.helps.add(helping)
        self.tuto.save()

        for helping in helps:
            response = self.client.get(reverse("content:helps") + f"?need={helping.slug}", follow=False)
            self.assertEqual(200, response.status_code)
            contents = response.context["contents"]
            self.assertEqual(len(contents), 1)

        # now, add an article
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user_author)
        article.subcategory.add(self.subcategory)
        article.save()

        # in the helps, there should still be only one results
        response = self.client.get(reverse("content:helps"), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 1)

        # test 'type' filter
        response = self.client.get(reverse("content:helps") + "?type=article", follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 0)  # no article yet

        response = self.client.get(reverse("content:helps") + "?type=tuto", follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 1)

        # add an help
        an_help = HelpWriting.objects.first()
        article.helps.add(an_help)
        article.save()

        response = self.client.get(reverse("content:helps"), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 2)  # ... then this time, we get two results !

        response = self.client.get(reverse("content:helps") + f"?need={an_help.slug}", follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 2)  # same with the help

        response = self.client.get(reverse("content:helps") + f"?need={HelpWriting.objects.last().slug}", follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 1)  # but only one if we ask for another need

        # test 'type' filter:
        response = self.client.get(reverse("content:helps") + "?type=article", follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 1)

        response = self.client.get(reverse("content:helps") + "?type=tuto", follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(len(contents), 1)

        # test pagination page doesn't exist
        response = self.client.get(reverse("content:helps") + "?page=1534", follow=False)
        self.assertEqual(404, response.status_code)

        # test pagination page not an integer
        response = self.client.get(reverse("content:helps") + "?page=abcd", follow=False)
        self.assertEqual(404, response.status_code)

    def test_help_tutorials_are_sorted_by_update_date(self):
        """This test checks that on the help page, the tutorials are sorted by update date"""
        a_help = HelpWritingFactory()
        a_help.save()

        temps_1 = datetime.datetime.now()
        temps_2 = temps_1 + datetime.timedelta(0, 1)

        tutoriel_1 = PublishableContentFactory(type="TUTORIAL")
        tutoriel_1.update_date = temps_1
        tutoriel_1.helps.add(a_help)
        tutoriel_1.save(update_date=False)

        tutoriel_2 = PublishableContentFactory(type="TUTORIAL")
        tutoriel_2.update_date = temps_2
        tutoriel_2.helps.add(a_help)
        tutoriel_2.save(update_date=False)

        response = self.client.get(reverse("content:helps"), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(contents[0], tutoriel_2)
        self.assertEqual(contents[1], tutoriel_1)

        tutoriel_1.update_date = temps_2
        tutoriel_2.update_date = temps_1
        tutoriel_1.save(update_date=False)
        tutoriel_2.save(update_date=False)

        response = self.client.get(reverse("content:helps"), follow=False)
        self.assertEqual(200, response.status_code)
        contents = response.context["contents"]
        self.assertEqual(contents[0], tutoriel_1)
        self.assertEqual(contents[1], tutoriel_2)

    def test_warn_typo(self):
        """
        Add a non-regression test about warning the author(s) of a typo in tutorial
        """

        typo_text = "Il y a une faute, c'est triste !"

        # create a tuto, populate, and set beta
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        self.client.force_login(self.user_author)

        sha_draft = PublishableContent.objects.get(pk=tuto.pk).sha_draft
        response = self.client.post(
            reverse("content:set-beta", kwargs={"pk": tuto.pk, "slug": tuto.slug}), {"version": sha_draft}, follow=False
        )
        self.assertEqual(302, response.status_code)
        sha_beta = PublishableContent.objects.get(pk=tuto.pk).sha_beta
        self.assertEqual(sha_draft, sha_beta)
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        # checks the user follow it
        self.assertEqual(TopicRead.objects.filter(topic__pk=tuto.beta_topic.pk).count(), 1)
        versioned = tuto.load_version(sha_beta)

        # check if author get error when warning typo on its own tutorial
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {"pk": tuto.pk, "version": sha_beta, "text": typo_text, "target": ""},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        # login with normal user
        self.client.logout()

        self.client.force_login(self.user_guest)

        # check the request to warn about a typo can't be a GET
        result = self.client.get(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {"pk": tuto.pk, "version": sha_beta, "text": typo_text, "target": ""},
            follow=True,
        )
        self.assertEqual(result.status_code, HttpResponseNotAllowed.status_code)

        # check the 'target' field in the request isn't mandatory
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {"pk": tuto.pk, "version": sha_beta, "text": typo_text},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {"pk": tuto.pk, "version": sha_beta, "text": typo_text, "target": ""},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(versioned.get_absolute_url_beta(), sent_pm.last_message.text)  # beta url is in message

        # check if user can warn typo in chapter of tutorial
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {"pk": tuto.pk, "version": sha_beta, "text": typo_text, "target": self.chapter1.get_path(relative=True)},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)
        self.chapter1.parent.parent = versioned
        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(self.chapter1.get_absolute_url_beta(), sent_pm.last_message.text)  # beta url is in message

        # now, induce change and publish
        self.client.force_login(self.user_author)

        ExtractFactory(container=self.chapter1, db_object=tuto)  # new extract

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": "valide moi ça, please", "version": versioned.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=tuto).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": "ça m'a l'air intéressant, je valide", "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=tuto).first()
        self.assertIsNotNone(published)

        # now, same stuffs on the public version
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()

        self.client.force_login(self.user_guest)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {"pk": tuto.pk, "version": tuto.sha_public, "text": typo_text, "target": ""},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(versioned.get_absolute_url_online(), sent_pm.last_message.text)  # online url is in message

        # check if user can warn typo in chapter of tutorial
        result = self.client.post(
            reverse("content:warn-typo") + f"?pk={tuto.pk}",
            {
                "pk": tuto.pk,
                "version": tuto.sha_public,
                "text": typo_text,
                "target": self.chapter1.get_path(relative=True),
            },
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(versioned.children[0].get_absolute_url_online(), sent_pm.last_message.text)

    def test_concurent_edition(self):
        """ensure that an edition is not successfull without provided the good `last_hash` to each form"""

        # create a tuto and populate
        tuto = PublishableContentFactory(type="TUTORIAL")
        tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=tuto.gallery, user=self.user_author, mode="W")
        tuto.licence = self.licence
        tuto.subcategory.add(self.subcategory)
        tuto.save()

        versioned = tuto.load_version()
        chapter = ContainerFactory(parent=versioned, db_object=tuto)
        extract = ExtractFactory(container=chapter, db_object=tuto)

        random = "Il est minuit 30 et j'écris un test ;)"
        random_with_md = "un text contenant du **markdown** ."

        self.client.force_login(self.user_author)

        # edit container:
        result = self.client.post(
            reverse(
                "content:edit-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": chapter.slug}
            ),
            {"title": chapter.title, "introduction": random, "conclusion": random, "last_hash": ""},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        chapter_version = tuto.load_version().children[0]
        self.assertNotEqual(chapter_version.get_introduction(), random)
        self.assertNotEqual(chapter_version.get_conclusion(), random)

        result = self.client.post(
            reverse(
                "content:edit-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": chapter.slug}
            ),
            {
                "title": chapter.title,
                "introduction": random,
                "conclusion": random,
                "last_hash": chapter_version.compute_hash(),
            },
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        chapter_version = tuto.load_version().children[0]
        self.assertEqual(chapter_version.get_introduction(), random)
        self.assertEqual(chapter_version.get_conclusion(), random)

        # preview
        result = self.client.post(
            reverse(
                "content:edit-extract",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "container_slug": chapter_version.slug,
                    "extract_slug": extract.slug,
                },
            ),
            {"title": random, "text": random_with_md, "last_hash": "", "preview": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(result.status_code, 200)

        result_string = "".join(a.decode() for a in result.streaming_content)
        self.assertIn("<strong>markdown</strong>", result_string, "We need the extract to be properly formatted")

        # edit extract
        result = self.client.post(
            reverse(
                "content:edit-extract",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "container_slug": chapter_version.slug,
                    "extract_slug": extract.slug,
                },
            ),
            {"title": random, "text": random, "last_hash": ""},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children[0].children[0]
        self.assertNotEqual(extract.get_text(), random)

        result = self.client.post(
            reverse(
                "content:edit-extract",
                kwargs={
                    "pk": tuto.pk,
                    "slug": tuto.slug,
                    "container_slug": chapter_version.slug,
                    "extract_slug": extract.slug,
                },
            ),
            {"title": random, "text": random, "last_hash": extract.compute_hash()},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children[0].children[0]
        self.assertEqual(extract.get_text(), random)

    def test_malformed_url(self):
        self.client.force_login(self.user_author)

        result = self.client.get(self.chapter1.get_absolute_url()[:-2] + "/")
        self.assertEqual(result.status_code, 404)
        result = self.client.get(self.part1.get_absolute_url()[:-2] + "/")
        self.assertEqual(result.status_code, 404)
        result = self.client.get(self.chapter1.get_absolute_url().replace(str(self.tuto.pk), "he-s-dead-jim"))
        self.assertEqual(result.status_code, 404)
        result = self.client.get(self.chapter1.get_absolute_url().replace(str(self.tuto.slug), "he-s-dead-jim"))
        self.assertEqual(result.status_code, 404)
        publishable = PublishedContentFactory(author_list=[self.user_author])
        published = PublishedContent.objects.filter(content_pk=publishable.pk).first()
        result = self.client.get(
            published.get_absolute_url_online().replace(str(published.content_public_slug), "he-s-dead-jim")
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(published.get_absolute_url_online().replace(str(published.content.pk), "1000000000"))
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            published.get_absolute_url_online().replace(str(published.content.pk), "he-s-dead-jim")
        )
        self.assertEqual(result.status_code, 404)
        self.client.force_login(self.user_guest)

        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={publishable.pk}",
            {"text": "message", "last_note": "0"},
            follow=True,
        )

        result = self.client.get(published.get_absolute_url_online() + "?page=2")
        self.assertEqual(result.status_code, 404)
        result = self.client.get(published.get_absolute_url_online() + "?page=clementine")
        self.assertEqual(result.status_code, 404)
        publishable = PublishableContentFactory(author_list=[self.user_author])
        result = self.client.get(publishable.get_absolute_url().replace(str(publishable.pk), "10000"))
        self.assertEqual(result.status_code, 404)
        result = self.client.get(publishable.get_absolute_url().replace(str(publishable.slug), "10000"))
        self.assertEqual(result.status_code, 403)  # get 403 since you're not author

        publishable = PublishedContentFactory(author_list=[self.user_author])
        old_date = publishable.update_date
        self.client.post(
            reverse("content:add-reaction") + f"?pk={publishable.pk}",
            {"text": "message", "last_note": "0"},
            follow=False,
        )
        publishable = PublishableContent.objects.get(pk=publishable.pk)
        self.assertEqual(old_date, publishable.update_date, "Erreur, le commentaire a entraîné une MAJ de la date!")
        # test antispam
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={publishable.pk}",
            {"text": "message", "last_note": str(publishable.last_note.pk)},
            follow=False,
        )
        self.assertEqual(result.status_code, 403)
        # test bad param
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={publishable.pk}",
            {"text": "message", "last_note": "I'm fine! I'm okay! This is all perfectly normal."},
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.post(
            reverse("content:add-reaction") + f"?pk={publishable.pk}",
            {"text": "message", "last_note": str(-5)},
            follow=False,
        )
        self.assertEqual(result.status_code, 200)

    def test_import_old_version(self):
        self.overridden_zds_app["content"]["default_licence_pk"] = LicenceFactory().pk

        self.client.force_login(self.user_author)
        base = settings.BASE_DIR / "fixtures" / "tuto"
        old_contents = [
            base / "article_v1",
            base / "balise_audio",
            base / "big_tuto_v1",
        ]
        for old_path in old_contents:
            draft_zip_path = old_path.with_suffix(".zip")
            shutil.make_archive(old_path, "zip", old_path)

            result = self.client.post(
                reverse("content:import-new"),
                {"archive": draft_zip_path.open("rb"), "subcategory": self.subcategory.pk},
                follow=False,
            )
            manifest = (old_path / "manifest.json").open("rb")
            json = json_handler.loads(manifest.read())
            manifest.close()
            self.assertEqual(result.status_code, 302)
            self.assertEqual(json["title"], PublishableContent.objects.last().title)

    def test_import_bad_archive(self):
        self.client.force_login(self.user_author)
        base = settings.BASE_DIR / "fixtures" / "tuto"
        old_path = base / "article_v1"

        shutil.move(old_path / "text.md", old_path / "text2.md")
        shutil.make_archive(old_path, "zip", old_path)
        shutil.move(old_path / "text2.md", old_path / "text.md")
        result = self.client.post(
            reverse("content:import-new"),
            {"archive": old_path.with_suffix(".zip").open("rb"), "subcategory": self.subcategory.pk},
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        msgs = result.context["messages"]
        levels = [msg.level for msg in msgs]
        self.assertIn(messages.ERROR, levels)

        shutil.copyfile(old_path / "manifest.json", old_path / "manifest2.json")
        with (old_path / "manifest.json").open("w") as man_file:
            man_file.write('{"version":2, "type":"Kitty Cat"}')
        shutil.make_archive(old_path, "zip", old_path)
        shutil.copyfile(old_path / "manifest2.json", old_path / "manifest.json")
        result = self.client.post(
            reverse("content:import-new"),
            {"archive": old_path.with_suffix(".zip").open("rb"), "subcategory": self.subcategory.pk},
            follow=False,
        )
        self.assertEqual(result.status_code, 200)
        msgs = result.context["messages"]
        levels = [msg.level for msg in msgs]
        self.assertIn(messages.ERROR, levels)

    def test_publication_make_extra_contents(self):
        """This test makes sure that the 'extra contents' (PDF, EPUB, ...) are generated by a publication
        while using a text containing images, and accessible !

        NOTE: this test will take time !"""
        PublicatorRegistry.registry["pdf"] = ZMarkdownRebberLatexPublicator(".pdf")
        PublicatorRegistry.registry["epub"] = ZMarkdownEpubPublicator()

        title = "C'est pas le plus important ici !"

        tuto = PublishableContentFactory(type="TUTORIAL")

        UserGalleryFactory(gallery=tuto.gallery, user=self.user_author, mode="W")
        tuto.licence = self.licence
        tuto.authors.add(self.user_author)
        tuto.save()

        versioned = tuto.load_version()

        # to be quick, instead of the views, we will use directly the code interface on this one !
        versioned.repo_update_top_container(tuto.title, tuto.slug, tricky_text_content, tricky_text_content)
        versioned.repo_add_container(title, tricky_text_content, tricky_text_content)
        chapter = versioned.children[-1]
        version = chapter.repo_add_extract(title, tricky_text_content)

        tuto.sha_draft = version
        tuto.save()

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": "Valide ?", "version": versioned.current_version},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=tuto).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept and publish. Will create the 'extra contents' !
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": "Je valide !", "is_major": True},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=tuto).first()
        self.assertIsNotNone(published)  # ok for the publication

        # test the presence of all 'extra contents'
        self.assertTrue(os.path.exists(published.get_prod_path()))
        self.assertTrue(os.path.exists(published.get_extra_contents_directory()))
        self.assertTrue(os.path.exists(os.path.join(published.get_extra_contents_directory(), "images")))

        avail_extra = ["md", "pdf", "epub", "zip"]

        # test existence and access for admin
        for extra in avail_extra:
            self.assertTrue(published.has_type(extra), msg=f'no extra content of format "{extra}" was found')
            result = self.client.get(published.get_absolute_url_to_extra_content(extra))
            self.assertEqual(result.status_code, 200)

        self.assertNotEqual(0, published.get_size_file_type("pdf"), msg="pdf must have content")
        self.assertNotEqual(0, published.get_size_file_type("epub"), msg="epub must have content")

        # test that deletion give a 404
        markdown_url = published.get_absolute_url_md()
        md_path = os.path.join(published.get_extra_contents_directory(), published.content_public_slug + ".md")
        os.remove(md_path)
        self.assertEqual(404, self.client.get(markdown_url).status_code)
        self.assertEqual("", published.get_absolute_url_to_extra_content("kboom"))
        self.client.logout()

        with open(md_path, "w") as f:  # remake a .md file, whatever the content
            f.write("I rebuilt it to finish the test. Perhaps a funny quote would be a good thing?")

        # same test with author:
        self.client.force_login(self.user_author)

        for extra in avail_extra:
            result = self.client.get(published.get_absolute_url_to_extra_content(extra))
            self.assertEqual(result.status_code, 200)
        # test for visitor:
        self.client.logout()

        # get 404 on markdown:
        result = self.client.get(published.get_absolute_url_to_extra_content("md"))
        self.assertEqual(result.status_code, 404)
        # md is for staff, html is not really supported
        # get 200 for the rest !
        for extra in avail_extra:
            if extra == "md":
                continue
            result = self.client.get(published.get_absolute_url_to_extra_content(extra))
            self.assertEqual(result.status_code, 200)

        # same test with guest:
        self.client.logout()
        self.client.force_login(self.user_guest)

        # get 404 on markdown:
        result = self.client.get(published.get_absolute_url_to_extra_content("md"))
        os.remove(os.path.join(published.get_extra_contents_directory(), published.content_public_slug + ".md"))
        self.assertEqual(result.status_code, 404)

        # get 200 for the rest !
        for extra in avail_extra:
            if extra == "md":
                continue
            result = self.client.get(published.get_absolute_url_to_extra_content(extra))
            self.assertEqual(result.status_code, 200, msg=f"Could not read {extra} export")

    def test_publication_give_pubdate_if_no_major(self):
        """if a content has never been published and `is_major` is not checked, still gives a publication date"""

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": "Valide ?", "version": tuto.sha_draft},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=tuto).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept and publish while unchecked the 'is_major'
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": "Je valide !", "is_major": False},  # !
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=tuto).first()
        self.assertIsNotNone(published)  # ok for the publication

        tuto = PublishableContent.objects.get(pk=tuto.pk)

        self.assertIsNotNone(tuto.pubdate)
        self.assertIsNotNone(published.publication_date)

        current_pubdate = tuto.pubdate
        ExtractFactory(container=self.chapter1, db_object=tuto)

        # connect with author:
        self.client.force_login(self.user_author)

        # ask validation
        result = self.client.post(
            reverse("validation:ask", kwargs={"pk": tuto.pk, "slug": tuto.slug}),
            {"text": "Valide ?", "version": tuto.sha_draft},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.client.force_login(self.user_staff)

        validation = Validation.objects.filter(content=tuto).last()

        result = self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # accept and publish while unchecked the 'is_major'
        result = self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": "Je valide !", "is_major": False},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=tuto).last()
        self.assertIsNotNone(published)  # ok for the publication

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertEqual(tuto.pubdate, current_pubdate)  # `is_major` in False → no update of the publication date

    def test_no_form_not_allowed(self):
        """Check that author cannot access to form that he is not allowed to in the creation process, because
        - The container already have child container and author ask to add a child extract ;
        - The container already contains child extract and author ask to add a container."""

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # connect with author:
        self.client.force_login(self.user_author)

        # create extract while there is already a part:
        result = self.client.get(reverse("content:create-extract", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 302)  # get redirection

        result = self.client.get(reverse("content:create-extract", args=[tuto.pk, tuto.slug]), follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)  # get an error message

        # create a container while there is already an extract:
        versioned = tuto.load_version()
        chapter = ContainerFactory(parent=versioned, db_object=tuto)
        ExtractFactory(container=chapter, db_object=tuto)

        result = self.client.get(
            reverse(
                "content:create-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": chapter.slug}
            ),
            follow=False,
        )
        self.assertEqual(result.status_code, 302)  # get redirection

        result = self.client.get(
            reverse(
                "content:create-container", kwargs={"pk": tuto.pk, "slug": tuto.slug, "container_slug": chapter.slug}
            ),
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        msgs = result.context["messages"]
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

    def test_gallery_not_deleted_if_linked_to_content(self):
        """Ensure that a gallery cannot be deleted if linked to a content"""
        gallery = Gallery.objects.get(pk=self.tuto.gallery.pk)
        self.assertIsNotNone(gallery)

        self.assertEqual(1, Gallery.objects.filter(pk=self.tuto.gallery.pk).count())

        # connect with author:
        self.client.force_login(self.user_author)

        # try to delete gallery
        result = self.client.post(reverse("gallery:delete"), {"delete": "", "gallery": gallery.pk}, follow=True)

        self.assertEqual(result.status_code, 403)
        self.assertEqual(1, Gallery.objects.filter(pk=self.tuto.gallery.pk).count())  # gallery not deleted

        # try to add to gallery
        result = self.client.post(
            reverse("gallery:members", kwargs={"pk": gallery.pk}),
            {"action": "add", "user": self.user_staff.username, "mode": "R"},
            follow=True,
        )

        self.assertEqual(result.status_code, 403)
        self.assertEqual(1, UserGallery.objects.filter(gallery=self.tuto.gallery).count())  # user not added

        # try to leave gallery
        result = self.client.post(
            reverse("gallery:members", kwargs={"pk": gallery.pk}),
            {
                "action": "leave",
                "user": self.user_author.username,
            },
            follow=True,
        )

        self.assertEqual(result.status_code, 403)
        self.assertEqual(1, UserGallery.objects.filter(gallery=self.tuto.gallery).count())  # user not deleted

    def test_delete_with_multiple_authors(self):
        """ensure that if more than one author, the user is just removed from list and the content is not deleted"""

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        new_author = ProfileFactory().user

        # login with author and add user
        self.client.force_login(self.user_author)

        result = self.client.post(
            reverse("content:add-author", args=[self.tuto.pk]), {"username": new_author.username}, follow=False
        )

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.authors.count(), 2)
        self.assertEqual(tuto.authors.filter(pk=new_author.pk).count(), 1)
        self.assertEqual(
            UserGallery.objects.filter(user=new_author, gallery=tuto.gallery).count(),
            1,
            "nb_author={}, nb_gallery={}, gallery_pk={}".format(
                tuto.authors.count(), UserGallery.objects.filter(gallery=tuto.gallery).count(), tuto.gallery.pk
            ),
        )

        # login with this new author, try to delete tuto
        self.client.force_login(new_author)

        # deleting
        result = self.client.post(reverse("content:delete", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.filter(pk=tuto.pk).count(), 1)  # not deleted

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertEqual(tuto.authors.count(), 1)  # it just delete the author from list
        self.assertEqual(tuto.authors.filter(pk=new_author.pk).count(), 0)
        self.assertEqual(UserGallery.objects.filter(user=new_author, gallery=tuto.gallery).count(), 0)

        # login with author
        self.client.logout()
        self.client.force_login(self.user_author)

        # now, will work
        result = self.client.post(reverse("content:delete", args=[tuto.pk, tuto.slug]), follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.filter(pk=tuto.pk).count(), 0)  # BOOM, deleted !

    def test_no_invalid_titles(self):
        """Test that invalid title (empty or wrong slugs) are not allowed"""

        # login with author
        self.client.force_login(self.user_author)

        dic = {
            "title": "",
            "description": "une description",
            "introduction": "une intro",
            "conclusion": "une conclusion",
            "type": "TUTORIAL",
            "licence": self.licence.pk,
            "subcategory": self.subcategory.pk,
        }

        # empty title not disallowed because it is converted to the default title
        disallowed_titles = ["-", "_", "__", "-_-", "$", "@", "&", "{}", "..."]

        for title in disallowed_titles:
            dic["title"] = title
            result = self.client.post(
                reverse("content:create-content", kwargs={"created_content_type": "TUTORIAL"}), dic, follow=False
            )
            self.assertEqual(result.status_code, 200)
            self.assertEqual(PublishableContent.objects.all().count(), 1)
            self.assertFalse(result.context["form"].is_valid())

        # Due to the internal use of `unicodedata.normalize()` by uuslug, some unicode characters are translated, and
        # therefor gives allowed titles, let's ensure that !
        # (see https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize and
        # https://github.com/un33k/python-slugify/blob/master/slugify/slugify.py#L117 for implementation !)
        allowed_titles = ["€€", "£€"]
        prev_count = 1

        for title in allowed_titles:
            dic["title"] = title
            result = self.client.post(
                reverse("content:create-content", kwargs={"created_content_type": "TUTORIAL"}), dic, follow=False
            )
            self.assertEqual(result.status_code, 302)
            self.assertNotEqual(PublishableContent.objects.all().count(), prev_count)
            prev_count += 1
