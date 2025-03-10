from os.path import dirname, isdir, isfile, join

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ContainerFactory, ExtractFactory, PublishableContentFactory
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


@override_for_contents()
class ContentMoveTests(TutorialTestMixin, TestCase):
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

    def test_move_up_extract(self):
        # login with author
        self.client.force_login(self.user_author)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.extract2 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        old_sha = tuto.sha_draft
        # test moving up smoothly
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract2.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "up",
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children[0]
        self.assertEqual(self.extract2.slug, extract.slug)
        # test moving up the first element
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract2.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "up",
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = (
            versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children_dict[self.extract2.slug]
        )
        self.assertEqual(1, extract.position_in_parent)

        # test moving without permission

        self.client.logout()
        self.client.force_login(self.user_guest)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract2.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "up",
                "pk": tuto.pk,
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

    def test_move_extract_before(self):
        # test 1 : move extract after a sibling
        # login with author
        self.client.force_login(self.user_author)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.extract2 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        self.extract3 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        old_sha = tuto.sha_draft
        # test moving smoothly
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "before:" + self.extract3.get_path(True)[:-3],
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children[0]
        self.assertEqual(self.extract2.slug, extract.slug)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        # test changing parent for extract (smoothly)
        self.chapter2 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract4 = ExtractFactory(container=self.chapter2, db_object=self.tuto)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "before:" + self.extract4.get_full_slug(),
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[0]
        self.assertEqual(self.extract1.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[1]
        self.assertEqual(self.extract4.slug, extract.slug)
        self.assertEqual(2, len(versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children))
        # test changing parents on a 'midsize content' (i.e depth of 1)
        midsize = PublishableContentFactory(author_list=[self.user_author])
        midsize_draft = midsize.load_version()
        first_container = ContainerFactory(parent=midsize_draft, db_object=midsize)
        second_container = ContainerFactory(parent=midsize_draft, db_object=midsize)
        first_extract = ExtractFactory(container=first_container, db_object=midsize)
        second_extract = ExtractFactory(container=second_container, db_object=midsize)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": first_extract.slug,
                "container_slug": first_container.get_path(True),
                "first_level_slug": "",
                "moving_method": "before:" + second_extract.get_full_slug(),
                "pk": midsize.pk,
            },
            follow=True,
        )
        self.assertEqual(result.status_code, 200)
        self.assertFalse(isfile(first_extract.get_path(True)))
        midsize = PublishableContent.objects.filter(pk=midsize.pk).first()
        midsize_draft = midsize.load_version()
        second_container_draft = midsize_draft.children[1]
        self.assertEqual(second_container_draft.children[0].title, first_extract.title)
        self.assertTrue(second_container_draft.children[0].get_path(False))

        # test try to move to a container that can't get extract
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter2.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "before:" + self.chapter1.get_path(True),
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[0]
        self.assertEqual(self.extract1.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[1]
        self.assertEqual(self.extract4.slug, extract.slug)
        self.assertEqual(2, len(versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children))
        # test try to move near an extract that does not exist
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter2.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "before:" + self.chapter1.get_path(True) + "/un-mauvais-extrait",
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(404, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[0]
        self.assertEqual(self.extract1.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[1]
        self.assertEqual(self.extract4.slug, extract.slug)
        self.assertEqual(2, len(versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children))

    def test_move_container_before(self):
        # login with author
        self.client.force_login(self.user_author)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.chapter2 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.chapter3 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.part2 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter4 = ContainerFactory(parent=self.part2, db_object=self.tuto)
        self.extract5 = ExtractFactory(container=self.chapter3, db_object=self.tuto)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        # test changing parent for container (smoothly)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.chapter3.slug,
                "container_slug": self.part1.slug,
                "first_level_slug": "",
                "moving_method": "before:" + self.chapter4.get_path(True),
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        self.assertEqual(2, len(versioned.children_dict[self.part2.slug].children))

        chapter = versioned.children_dict[self.part2.slug].children[0]
        self.assertTrue(isdir(chapter.get_path()))
        self.assertEqual(1, len(chapter.children))
        self.assertTrue(isfile(chapter.children[0].get_path()))
        self.assertEqual(self.extract5.slug, chapter.children[0].slug)
        self.assertEqual(self.chapter3.slug, chapter.slug)
        chapter = versioned.children_dict[self.part2.slug].children[1]
        self.assertEqual(self.chapter4.slug, chapter.slug)
        # test changing parent for too deep container
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.part1.slug,
                "container_slug": self.tuto.slug,
                "first_level_slug": "",
                "moving_method": "before:" + self.chapter4.get_path(True),
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(200, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        self.assertEqual(2, len(versioned.children_dict[self.part2.slug].children))
        chapter = versioned.children_dict[self.part2.slug].children[0]
        self.assertEqual(self.chapter3.slug, chapter.slug)
        chapter = versioned.children_dict[self.part2.slug].children[1]
        self.assertEqual(self.chapter4.slug, chapter.slug)

        # test moving before the root
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.part1.slug,
                "container_slug": self.tuto.slug,
                "first_level_slug": "",
                "moving_method": "before:" + self.tuto.load_version().get_path(),
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(404, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        self.assertEqual(2, len(versioned.children_dict[self.part2.slug].children))
        chapter = versioned.children_dict[self.part2.slug].children[0]
        self.assertEqual(self.chapter3.slug, chapter.slug)
        chapter = versioned.children_dict[self.part2.slug].children[1]
        self.assertEqual(self.chapter4.slug, chapter.slug)

        # test moving without permission

        self.client.logout()
        self.client.force_login(self.user_guest)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.chapter2.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "up",
                "pk": tuto.pk,
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 403)

    def test_move_extract_after(self):
        # test 1 : move extract after a sibling
        # login with author
        self.client.force_login(self.user_author)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.extract2 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        self.extract3 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        old_sha = tuto.sha_draft
        # test moving smoothly
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "after:" + self.extract3.get_path(True)[:-3],
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children[0]
        self.assertEqual(self.extract2.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children[1]
        self.assertEqual(self.extract3.slug, extract.slug)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        # test changing parent for extract (smoothly)
        self.chapter2 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.extract4 = ExtractFactory(container=self.chapter2, db_object=self.tuto)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter1.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "after:" + self.extract4.get_path(True)[:-3],
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[1]
        self.assertEqual(self.extract1.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[0]
        self.assertEqual(self.extract4.slug, extract.slug)
        self.assertEqual(2, len(versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children))
        # test try to move to a container that can't get extract
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter2.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "after:" + self.chapter1.get_path(True),
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[1]
        self.assertEqual(self.extract1.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[0]
        self.assertEqual(self.extract4.slug, extract.slug)
        self.assertEqual(2, len(versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children))
        # test try to move near an extract that does not exist
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.extract1.slug,
                "container_slug": self.chapter2.slug,
                "first_level_slug": self.part1.slug,
                "moving_method": "after:" + self.chapter1.get_path(True) + "/un-mauvais-extrait",
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(404, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[1]
        self.assertEqual(self.extract1.slug, extract.slug)
        extract = versioned.children_dict[self.part1.slug].children_dict[self.chapter2.slug].children[0]
        self.assertEqual(self.extract4.slug, extract.slug)
        self.assertEqual(2, len(versioned.children_dict[self.part1.slug].children_dict[self.chapter1.slug].children))

    def test_move_container_after(self):
        # login with author
        self.client.force_login(self.user_author)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.chapter2 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.chapter3 = ContainerFactory(parent=self.part1, db_object=self.tuto)
        self.part2 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.extract5 = ExtractFactory(container=self.chapter3, db_object=self.tuto)
        self.chapter4 = ContainerFactory(parent=self.part2, db_object=self.tuto)
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        # test changing parent for container (smoothly)
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.chapter3.slug,
                "container_slug": self.part1.slug,
                "first_level_slug": "",
                "moving_method": "after:" + self.chapter4.get_path(True),
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(200, result.status_code)
        self.assertNotEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        self.assertEqual(2, len(versioned.children_dict[self.part2.slug].children))
        chapter = versioned.children_dict[self.part2.slug].children[1]
        self.assertEqual(1, len(chapter.children))
        self.assertTrue(isfile(chapter.children[0].get_path()))
        self.assertEqual(self.extract5.slug, chapter.children[0].slug)
        self.assertEqual(self.chapter3.slug, chapter.slug)
        chapter = versioned.children_dict[self.part2.slug].children[0]
        self.assertEqual(self.chapter4.slug, chapter.slug)
        # test changing parent for too deep container
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        old_sha = tuto.sha_draft
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": self.part1.slug,
                "container_slug": self.tuto.slug,
                "first_level_slug": "",
                "moving_method": "after:" + self.chapter4.get_path(True),
                "pk": tuto.pk,
            },
            follow=True,
        )

        self.assertEqual(200, result.status_code)
        self.assertEqual(old_sha, PublishableContent.objects.get(pk=tuto.pk).sha_draft)
        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        self.assertEqual(2, len(versioned.children_dict[self.part2.slug].children))
        chapter = versioned.children_dict[self.part2.slug].children[1]
        self.assertEqual(self.chapter3.slug, chapter.slug)
        chapter = versioned.children_dict[self.part2.slug].children[0]
        self.assertEqual(self.chapter4.slug, chapter.slug)

    def test_move_no_slug_update(self):
        """
        this test comes from issue #3328 (https://github.com/zestedesavoir/zds-site/issues/3328)
        telling it is tricky is kind of euphemism.
        :return:
        """
        LicenceFactory(code="CC BY")
        self.client.force_login(self.user_author)
        draft_zip_path = join(dirname(__file__), "fake_lasynchrone-et-le-multithread-en-net.zip")
        result = self.client.post(
            reverse("content:import-new"),
            {"archive": open(draft_zip_path, "rb"), "subcategory": self.subcategory.pk},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        tuto = PublishableContent.objects.last()
        published = publish_content(tuto, tuto.load_version(), True)
        tuto.sha_public = tuto.sha_draft
        tuto.public_version = published
        tuto.save()
        extract1 = tuto.load_version().children[0]
        # test moving up smoothly
        result = self.client.post(
            reverse("content:move-element"),
            {
                "child_slug": extract1.slug,
                "first_level_slug": "",
                "container_slug": tuto.slug,
                "moving_method": "down",
                "pk": tuto.pk,
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertTrue(isdir(tuto.get_repo_path()))
