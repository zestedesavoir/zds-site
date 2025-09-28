import os
import unittest
from datetime import datetime, timedelta

from django.conf import settings
from django.template.defaultfilters import date
from django.test import TestCase
from django.urls import reverse

from zds.gallery.models import UserGallery
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublishableContent, PublishedContent
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ExtractFactory,
    PublishableContentFactory,
    PublishedContentFactory,
)
from zds.utils.models import Tag
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


@override_for_contents()
class ContentTests(TutorialTestMixin, TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.mas = ProfileFactory().user
        self.overridden_zds_app["member"]["bot_account"] = self.mas.username

        self.licence = LicenceFactory()

        self.user_author = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user_author, mode="W")
        self.tuto.licence = self.licence
        self.tuto.save()

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

    def test_workflow_content(self):
        """
        General tests for a content
        """
        # ensure the usability of manifest
        versioned = self.tuto.load_version()
        self.assertEqual(self.tuto_draft.title, versioned.title)
        self.assertEqual(self.part1.title, versioned.children[0].title)
        self.assertEqual(self.extract1.title, versioned.children[0].children[0].children[0].title)

        # ensure url resolution project using dictionary:
        self.assertTrue(self.part1.slug in list(versioned.children_dict.keys()))
        self.assertTrue(self.chapter1.slug in versioned.children_dict[self.part1.slug].children_dict)

    def test_slug_pool(self):
        versioned = self.tuto.load_version()

        for i in [1, 2, 3]:
            slug = "introduction-" + str(i)
            self.assertEqual(slug, versioned.get_unique_slug("introduction"))
            self.assertTrue(slug in versioned.slug_pool)

    def test_ensure_unique_slug(self):
        """
        Ensure that slugs for a container or extract are always unique
        """
        # get draft version
        versioned = self.tuto.load_version()

        # forbidden slugs:
        slug_to_test = ["introduction", "conclusion"]

        for slug in slug_to_test:
            new_slug = versioned.get_unique_slug(slug)
            self.assertNotEqual(slug, new_slug)
            self.assertTrue(new_slug in versioned.slug_pool)  # ensure new slugs are in slug pool

        # then test with 'real' containers and extracts:
        new_chapter_1 = ContainerFactory(title="aa", parent=versioned, db_object=self.tuto)
        new_chapter_2 = ContainerFactory(title="aa", parent=versioned, db_object=self.tuto)
        self.assertNotEqual(new_chapter_1.slug, new_chapter_2.slug)
        new_extract_1 = ExtractFactory(title="aa", container=new_chapter_1, db_object=self.tuto)
        self.assertEqual(new_extract_1.slug, new_chapter_1.slug)  # different level can have the same slug!

        new_extract_2 = ExtractFactory(title="aa", container=new_chapter_2, db_object=self.tuto)
        self.assertEqual(new_extract_2.slug, new_extract_1.slug)  # not the same parent, so allowed

        new_extract_3 = ExtractFactory(title="aa", container=new_chapter_1, db_object=self.tuto)
        self.assertNotEqual(new_extract_3.slug, new_extract_1.slug)  # same parent, forbidden

    def test_ensure_unique_slug_2(self):
        """This test is an extension of the previous one, with the manifest reloaded each time"""

        title = "Il existe des gens que la ZEP-12 n'aime pas"
        random = "... Mais c'est pas censé arriver, donc on va tout faire pour que ça disparaisse !"

        # get draft version
        versioned = self.tuto.load_version()

        # add containers
        version = versioned.repo_add_container(title, random, random)
        new_version = self.tuto.load_version(sha=version)
        self.assertEqual(new_version.children[-1].slug, versioned.children[-1].slug)

        slugs = [new_version.children[-1].slug]

        for i in range(0, 2):  # will add 3 new container
            with self.subTest(f"subcontainer {i}"):
                version = versioned.repo_add_container(title, random, random)
                new_version = self.tuto.load_version(sha=version)
                self.assertEqual(new_version.children[-1].slug, versioned.children[-1].slug)
                self.assertTrue(new_version.children[-1].slug not in slugs)  # slug is different
                self.assertTrue(versioned.children[-1].slug not in slugs)

                slugs.append(new_version.children[-1].slug)

        # add extracts
        extract_title = "On va changer de titre (parce qu'on sais jamais) !"

        chapter = versioned.children[-1]  # for this second test, the last chapter will be used
        version = chapter.repo_add_extract(extract_title, random)
        new_version = self.tuto.load_version(sha=version)
        self.assertEqual(new_version.children[-1].children[-1].slug, chapter.children[-1].slug)

        slugs = [new_version.children[-1].children[-1].slug]

        for i in range(0, 2):  # will add 3 new extracts with the same title
            version = chapter.repo_add_extract(extract_title, random)
            new_version = self.tuto.load_version(sha=version)
            self.assertTrue(new_version.children[-1].children[-1].slug not in slugs)
            self.assertTrue(chapter.children[-1].slug not in slugs)

            slugs.append(new_version.children[-1].children[-1].slug)

    def test_workflow_repository(self):
        """
        Test to ensure the behavior of repo_*() functions:
        - if they change the filesystem as they are suppose to ;
        - if they change the `self.sha_*` as they are suppose to.
        """

        new_title = "Un nouveau titre"
        other_new_title = "Un titre différent"
        random_text = "J'ai faim!"
        other_random_text = "Oh, du chocolat <3"

        versioned = self.tuto.load_version()
        current_version = versioned.current_version
        slug_repository = versioned.slug_repository

        # VersionedContent:
        old_path = versioned.get_path()
        self.assertTrue(os.path.isdir(old_path))
        new_slug = versioned.get_unique_slug(new_title)  # normally, you get a new slug by asking database!

        versioned.repo_update_top_container(new_title, new_slug, random_text, random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        new_path = versioned.get_path()
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isdir(new_path))
        self.assertFalse(os.path.isdir(old_path))

        self.assertNotEqual(slug_repository, versioned.slug_repository)  # if this test fail, you're in trouble

        # Container:

        # 1. add new part:
        versioned.repo_add_container(new_title, random_text, random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        part = versioned.children[-1]
        old_path = part.get_path()
        self.assertTrue(os.path.isdir(old_path))
        self.assertTrue(os.path.exists(os.path.join(versioned.get_path(), part.introduction)))
        self.assertTrue(os.path.exists(os.path.join(versioned.get_path(), part.conclusion)))
        self.assertEqual(part.get_introduction(), random_text)
        self.assertEqual(part.get_conclusion(), random_text)

        # 2. update the part
        part.repo_update(other_new_title, other_random_text, other_random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        new_path = part.get_path()
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isdir(new_path))
        self.assertFalse(os.path.isdir(old_path))

        self.assertEqual(part.get_introduction(), other_random_text)
        self.assertEqual(part.get_conclusion(), other_random_text)

        # 3. delete it
        part.repo_delete()  # boom!
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        self.assertFalse(os.path.isdir(new_path))

        # Extract:

        # 1. add new extract
        versioned.repo_add_container(new_title, random_text, random_text)  # need to add a new part before
        part = versioned.children[-1]

        part.repo_add_extract(new_title, random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        extract = part.children[-1]
        old_path = extract.get_path()
        self.assertTrue(os.path.isfile(old_path))
        self.assertEqual(extract.get_text(), random_text)

        # 2. update extract
        extract.repo_update(other_new_title, other_random_text)
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)
        current_version = versioned.current_version

        new_path = extract.get_path()
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isfile(new_path))
        self.assertFalse(os.path.isfile(old_path))

        self.assertEqual(extract.get_text(), other_random_text)

        # 3. update parent and see if it still works:
        part.repo_update(other_new_title, other_random_text, other_random_text)

        old_path = new_path
        new_path = extract.get_path()

        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.isfile(new_path))
        self.assertFalse(os.path.isfile(old_path))

        self.assertEqual(extract.get_text(), other_random_text)

        # 4. Boom, no more extract
        extract.repo_delete()
        self.assertNotEqual(versioned.sha_draft, current_version)
        self.assertNotEqual(versioned.current_version, current_version)
        self.assertEqual(versioned.current_version, versioned.sha_draft)

        self.assertFalse(os.path.exists(new_path))

    def test_if_none(self):
        """Test the case where introduction and conclusion are `None`"""

        given_title = "La vie secrète de Clem'"
        some_text = "Tous ces secrets (ou pas)"
        versioned = self.tuto.load_version()
        # add a new part with `None` for intro and conclusion
        version = versioned.repo_add_container(given_title, None, None)

        # check on the model:
        new_part = versioned.children[-1]
        self.assertIsNone(new_part.introduction)
        self.assertIsNone(new_part.conclusion)

        # it remains when loading the manifest!
        versioned2 = self.tuto.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNone(versioned.children[-1].introduction)
        self.assertIsNone(versioned.children[-1].conclusion)

        version = new_part.repo_update(given_title, None, None)  # still `None`
        self.assertIsNone(new_part.introduction)
        self.assertIsNone(new_part.conclusion)

        # does it still remains?
        versioned2 = self.tuto.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNone(versioned.children[-1].introduction)
        self.assertIsNone(versioned.children[-1].conclusion)

        new_part.repo_update(given_title, some_text, some_text)
        self.assertIsNotNone(new_part.introduction)  # now, value given
        self.assertIsNotNone(new_part.conclusion)

        old_intro = new_part.introduction
        old_conclu = new_part.conclusion
        self.assertTrue(os.path.isfile(os.path.join(versioned.get_path(), old_intro)))
        self.assertTrue(os.path.isfile(os.path.join(versioned.get_path(), old_conclu)))

        # when loaded the manifest, not None, this time
        versioned2 = self.tuto.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNotNone(versioned.children[-1].introduction)
        self.assertIsNotNone(versioned.children[-1].conclusion)

        version = new_part.repo_update(given_title, None, None)  # and we go back to `None`
        self.assertIsNone(new_part.introduction)
        self.assertIsNone(new_part.conclusion)
        self.assertFalse(os.path.isfile(os.path.join(versioned.get_path(), old_intro)))  # introduction is deleted
        self.assertFalse(os.path.isfile(os.path.join(versioned.get_path(), old_conclu)))

        # does it go back to None?
        versioned2 = self.tuto.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNone(versioned.children[-1].introduction)
        self.assertIsNone(versioned.children[-1].conclusion)

        new_part.repo_update(given_title, "", "")  # '' is not None
        self.assertIsNotNone(new_part.introduction)
        self.assertIsNotNone(new_part.conclusion)

    def test_extract_is_none(self):
        """Test the case of a null extract"""

        article = PublishableContentFactory(type="ARTICLE")
        versioned = article.load_version()

        given_title = "Peu importe, en fait, ça compte peu"
        some_text = "Disparaitra aussi vite que possible"

        # add a new extract with `None` for text
        version = versioned.repo_add_extract(given_title, None)

        # check on the model:
        new_extract = versioned.children[-1]
        self.assertIsNone(new_extract.text)

        # it remains when loading the manifest!
        versioned2 = article.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNone(versioned.children[-1].text)

        version = new_extract.repo_update(given_title, None)
        self.assertIsNone(new_extract.text)

        # it remains
        versioned2 = article.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNone(versioned.children[-1].text)

        version = new_extract.repo_update(given_title, some_text)
        self.assertIsNotNone(new_extract.text)
        self.assertEqual(some_text, new_extract.get_text())

        # now it changes
        versioned2 = article.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNotNone(versioned.children[-1].text)

        # ... and lets go back
        version = new_extract.repo_update(given_title, None)
        self.assertIsNone(new_extract.text)

        # it has changed
        versioned2 = article.load_version(sha=version)
        self.assertIsNotNone(versioned2)
        self.assertIsNone(versioned.children[-1].text)

    def test_ensure_slug_stay(self):
        """This test ensures that slugs are not modified when coming from a manifest"""

        tuto = PublishableContentFactory(type="TUTORIAL")
        versioned = tuto.load_version()

        random = "Non, piti bug, tu ne reviendras plus !!!"
        title = "N'importe quel titre"

        # add three container with the same title
        versioned.repo_add_container(title, random, random)  # x
        versioned.repo_add_container(title, random, random)  # x-1
        version = versioned.repo_add_container(title, random, random)  # x-2
        self.assertEqual(len(versioned.children), 3)

        current = tuto.load_version(sha=version)
        self.assertEqual(len(current.children), 3)

        for index, child in enumerate(current.children):
            self.assertEqual(child.slug, versioned.children[index].slug)  # same order

        # then, delete the second one:
        last_slug = versioned.children[2].slug
        version = versioned.children[1].repo_delete()
        self.assertEqual(len(versioned.children), 2)
        self.assertEqual(versioned.children[1].slug, last_slug)

        current = tuto.load_version(sha=version)
        self.assertEqual(len(current.children), 2)

        for index, child in enumerate(current.children):
            self.assertEqual(child.slug, versioned.children[index].slug)  # slug remains

        # same test with extracts
        chapter = versioned.children[0]
        chapter.repo_add_extract(title, random)  # x
        chapter.repo_add_extract(title, random)  # x-1
        version = chapter.repo_add_extract(title, random)  # x-2
        self.assertEqual(len(chapter.children), 3)

        current = tuto.load_version(sha=version)
        self.assertEqual(len(current.children[0].children), 3)

        for index, child in enumerate(current.children[0].children):
            self.assertEqual(child.slug, chapter.children[index].slug)  # slug remains

        # delete the second one!
        last_slug = chapter.children[2].slug
        version = chapter.children[1].repo_delete()
        self.assertEqual(len(chapter.children), 2)
        self.assertEqual(chapter.children[1].slug, last_slug)

        current = tuto.load_version(sha=version)
        self.assertEqual(len(current.children[0].children), 2)

        for index, child in enumerate(current.children[0].children):
            self.assertEqual(child.slug, chapter.children[index].slug)  # slug remains for extract as well!

    def test_publication_and_attributes_consistency(self):
        pubdate = datetime.now() - timedelta(days=1)
        article = PublishedContentFactory(type="ARTICLE", author_list=[self.user_author])
        public_version = article.public_version
        public_version.publication_date = pubdate
        public_version.save()
        # everything must come from database to have good datetime comparison
        article = PublishableContent.objects.get(pk=article.pk)
        article.public_version.load_public_version()
        old_date = article.public_version.publication_date
        old_title = article.public_version.title()
        old_description = article.public_version.description()
        article.licence = LicenceFactory()
        article.save()

        self.client.force_login(self.user_author)

        new_title = old_title + "bla"
        result = self.client.post(
            reverse("content:edit-title", args=[article.pk]),
            {"title": new_title},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        new_description = old_description + "bla"
        result = self.client.post(
            reverse("content:edit-subtitle", args=[article.pk]),
            {"subtitle": new_description},
            follow=True,
        )
        self.assertEqual(result.status_code, 200)

        article = PublishableContent.objects.prefetch_related("public_version").get(pk=article.pk)
        article.public_version.load_public_version()
        self.assertEqual(old_title, article.public_version.title())
        self.assertEqual(old_description, article.public_version.description())
        self.assertEqual(old_date, article.public_version.publication_date)

        publish_content(article, article.load_version(), False)

        article = PublishableContent.objects.prefetch_related("public_version").get(pk=article.pk)
        self.assertEqual(old_date, article.public_version.publication_date)
        self.assertNotEqual(old_date, article.public_version.update_date)

    def test_add_tags(self):
        tuto = self.tuto
        tags_len = len(Tag.objects.all())
        tuto_tags_len = len(tuto.tags.all())

        # add 3 tags
        tags = ["a", "b", "c"]
        tuto.add_tags(tags)
        tags_len += 3
        tuto_tags_len += 3
        self.assertEqual(tags_len, len(Tag.objects.all()))
        self.assertEqual(tuto_tags_len, len(tuto.tags.all()))

        # add the same tags (nothing append)
        tags = ["a", "b", "c"]
        tuto.add_tags(tags)
        self.assertEqual(tags_len, len(Tag.objects.all()))
        self.assertEqual(tuto_tags_len, len(tuto.tags.all()))

        # add 2 more
        tags = ["d", "e"]
        tuto.add_tags(tags)
        tags_len += 2
        tuto_tags_len += 2
        self.assertEqual(tags_len, len(Tag.objects.all()))
        self.assertEqual(tuto_tags_len, len(tuto.tags.all()))

        # add 3 with invalid content (only 2 valid)
        tags = ["f", "g", " "]
        tuto.add_tags(tags)
        tags_len += 2
        tuto_tags_len += 2
        self.assertEqual(
            tags_len, Tag.objects.count(), 'all tags are "{}"'.format('","'.join([str(t) for t in Tag.objects.all()]))
        )
        self.assertEqual(tuto_tags_len, len(tuto.tags.all()))

        # test space in tags (first and last space deleted)
        tags = ["foo bar", " azerty", "qwerty ", " another tag "]
        tuto.add_tags(tags)
        tuto_tags_list = [tag["title"] for tag in tuto.tags.values("title")]
        self.assertIn("foo bar", tuto_tags_list)
        self.assertNotIn(" azerty", tuto_tags_list)
        self.assertIn("azerty", tuto_tags_list)
        self.assertNotIn("qwerty ", tuto_tags_list)
        self.assertIn("qwerty", tuto_tags_list)
        self.assertNotIn(" another tag", tuto_tags_list)
        self.assertIn("another tag", tuto_tags_list)

    @unittest.skip("The test seems to be incorrect in its way to count chars")
    def test_char_count_after_publication(self):
        """Test the ``get_char_count()`` function.

        Special care should be taken with this function, since:

        - The username of the author is, by default "Firmxxx" where "xxx" depends on the tests before ;
        - The titles (!) also contains a number that also depends on the number of tests before ;
        - The date is ``datetime.now()`` and contains the months, which is never a fixed number of letters.
        """

        author = ProfileFactory().user
        author.username = "NotAFirm1Clone"
        author.save()

        len_date_now = len(date(datetime.now(), "d F Y"))

        article = PublishedContentFactory(type="ARTICLE", author_list=[author], title="Un titre")
        published = PublishedContent.objects.filter(content=article).first()
        self.assertEqual(published.get_char_count(), 160 + len_date_now)

        tuto = PublishableContentFactory(type="TUTORIAL", author_list=[author], title="Un titre")

        # add a chapter, so it becomes a middle tutorial
        tuto_draft = tuto.load_version()
        chapter1 = ContainerFactory(parent=tuto_draft, db_object=tuto, title="Un chapitre")
        ExtractFactory(container=chapter1, db_object=tuto, title="Un extrait")
        published = publish_content(tuto, tuto_draft, is_major_update=True)

        tuto.sha_public = tuto_draft.current_version
        tuto.sha_draft = tuto_draft.current_version
        tuto.public_version = published
        tuto.save()

        published = PublishedContent.objects.filter(content=tuto).first()
        self.assertEqual(published.get_char_count(), 335 + len_date_now)

    def test_ensure_gallery(self):
        content = PublishedContentFactory()
        content.authors.add(ProfileFactory().user)
        content.authors.add(ProfileFactory().user)
        content.save()
        content.ensure_author_gallery()
        self.assertEqual(UserGallery.objects.filter(gallery__pk=content.gallery.pk).count(), content.authors.count())
        content.authors.add(ProfileFactory().user)
        content.save()
        content.ensure_author_gallery()
        self.assertEqual(UserGallery.objects.filter(gallery__pk=content.gallery.pk).count(), content.authors.count())
