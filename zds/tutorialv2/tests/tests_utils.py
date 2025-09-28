import datetime
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from zds import json_handler
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import ContentReaction, ContentRead, PublishableContent, PublishedContent
from zds.tutorialv2.models.versioned import Container
from zds.tutorialv2.publication_utils import (
    Publicator,
    PublicatorRegistry,
    ZMarkdownRebberLatexPublicator,
    publish_content,
    unpublish_content,
)
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ContentReactionFactory,
    ExtractFactory,
    PublishableContentFactory,
    PublishedContentFactory,
)
from zds.tutorialv2.utils import (
    BadManifestError,
    get_commit_author,
    get_content_from_json,
    get_target_tagged_tree_for_container,
    get_target_tagged_tree_for_extract,
    last_participation_is_old,
)
from zds.utils.header_notifications import get_header_notifications
from zds.utils.models import Alert
from zds.utils.tests.factories import LicenceFactory
from zds.utils.validators import InvalidSlugError, check_slug, slugify_raise_on_invalid


@override_for_contents()
class UtilsTests(TutorialTestMixin, TestCase):
    def setUp(self):
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
        self.old_registry = {key: value for key, value in PublicatorRegistry.get_all_registered()}

        class TestPdfPublicator(Publicator):
            def publish(self, md_file_path, base_name, **kwargs):
                with Path(base_name + ".pdf").open("w") as f:
                    f.write("bla")
                shutil.copy2(str(Path(base_name + ".pdf")), str(Path(md_file_path.replace("__building", "")).parent))

        PublicatorRegistry.registry["pdf"] = TestPdfPublicator()

    def test_get_target_tagged_tree_for_container(self):
        part2 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto, title="part2")
        part3 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto, title="part3")
        tagged_tree = get_target_tagged_tree_for_container(self.part1, self.tuto_draft)

        self.assertEqual(4, len(tagged_tree))
        paths = {i[0]: i[3] for i in tagged_tree}
        self.assertTrue(part2.get_path(True) in paths)
        self.assertTrue(part3.get_path(True) in paths)
        self.assertTrue(self.chapter1.get_path(True) in paths)
        self.assertTrue(self.part1.get_path(True) in paths)
        self.assertFalse(self.tuto_draft.get_path(True) in paths)
        self.assertFalse(paths[self.chapter1.get_path(True)], "can't be moved to a too deep container")
        self.assertFalse(paths[self.part1.get_path(True)], "can't be moved after or before himself")
        self.assertTrue(paths[part2.get_path(True)], "can be moved after or before part2")
        self.assertTrue(paths[part3.get_path(True)], "can be moved after or before part3")
        tagged_tree = get_target_tagged_tree_for_container(part3, self.tuto_draft)
        self.assertEqual(4, len(tagged_tree))
        paths = {i[0]: i[3] for i in tagged_tree}
        self.assertTrue(part2.get_path(True) in paths)
        self.assertTrue(part3.get_path(True) in paths)
        self.assertTrue(self.chapter1.get_path(True) in paths)
        self.assertTrue(self.part1.get_path(True) in paths)
        self.assertFalse(self.tuto_draft.get_path(True) in paths)
        self.assertTrue(paths[self.chapter1.get_path(True)], "can't be moved to a too deep container")
        self.assertTrue(paths[self.part1.get_path(True)], "can't be moved after or before himself")
        self.assertTrue(paths[part2.get_path(True)], "can be moved after or before part2")
        self.assertFalse(paths[part3.get_path(True)], "can be moved after or before part3")

    def test_publish_content_article(self):
        """test and ensure the behavior of ``publish_content()`` and ``unpublish_content()``"""

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

        self.assertEqual(len(article_draft.children), 2)

        # publish !
        article = PublishableContent.objects.get(pk=article.pk)
        published = publish_content(article, article_draft)

        self.assertEqual(published.content, article)
        self.assertEqual(published.content_pk, article.pk)
        self.assertEqual(published.content_type, article.type)
        self.assertEqual(published.content_public_slug, article_draft.slug)
        self.assertEqual(published.sha_public, article.sha_draft)

        public = article.load_version(sha=published.sha_public, public=published)
        self.assertIsNotNone(public)
        self.assertTrue(public.PUBLIC)  # it's a PublicContent object
        self.assertEqual(public.type, published.content_type)
        self.assertEqual(public.current_version, published.sha_public)

        # test object created in database
        self.assertEqual(PublishedContent.objects.filter(content=article).count(), 1)
        published = PublishedContent.objects.filter(content=article).last()

        self.assertEqual(published.content_pk, article.pk)
        self.assertEqual(published.content_public_slug, article_draft.slug)
        self.assertEqual(published.content_type, article.type)
        self.assertEqual(published.sha_public, public.current_version)

        # test creation of files:
        self.assertTrue(os.path.isdir(published.get_prod_path()))
        self.assertTrue(os.path.isfile(os.path.join(published.get_prod_path(), "manifest.json")))
        prod_path = public.get_prod_path()
        self.assertTrue(prod_path.endswith(".html"), prod_path)
        self.assertTrue(os.path.isfile(prod_path), prod_path)  # normally, an HTML file should exists
        self.assertIsNone(public.introduction)  # since all is in the HTML file, introduction does not exists anymore
        self.assertIsNone(public.conclusion)
        article.public_version = published
        article.save()
        # depublish it !
        unpublish_content(article)
        self.assertEqual(PublishedContent.objects.filter(content=article).count(), 0)  # published object disappear
        self.assertFalse(os.path.exists(public.get_prod_path()))  # article was removed
        # ... For the next tests, I will assume that the unpublication works.

    def test_publish_content_medium_tuto(self):
        # 3. Medium-size tutorial
        midsize_tuto = PublishableContentFactory(type="TUTORIAL")

        midsize_tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=midsize_tuto.gallery, user=self.user_author, mode="W")
        midsize_tuto.licence = self.licence
        midsize_tuto.save()

        # populate with 2 chapters (1 extract each)
        midsize_tuto_draft = midsize_tuto.load_version()
        chapter1 = ContainerFactory(parent=midsize_tuto_draft, db_object=midsize_tuto)
        ExtractFactory(container=chapter1, db_object=midsize_tuto)
        chapter2 = ContainerFactory(parent=midsize_tuto_draft, db_object=midsize_tuto)
        ExtractFactory(container=chapter2, db_object=midsize_tuto)

        # publish it
        midsize_tuto = PublishableContent.objects.get(pk=midsize_tuto.pk)
        published = publish_content(midsize_tuto, midsize_tuto_draft)

        self.assertEqual(published.content, midsize_tuto)
        self.assertEqual(published.content_pk, midsize_tuto.pk)
        self.assertEqual(published.content_type, midsize_tuto.type)
        self.assertEqual(published.content_public_slug, midsize_tuto_draft.slug)
        self.assertEqual(published.sha_public, midsize_tuto.sha_draft)

        public = midsize_tuto.load_version(sha=published.sha_public, public=published)
        self.assertIsNotNone(public)
        self.assertTrue(public.PUBLIC)  # it's a PublicContent object
        self.assertEqual(public.type, published.content_type)
        self.assertEqual(public.current_version, published.sha_public)

        # test creation of files:
        self.assertTrue(Path(published.get_prod_path()).is_dir())
        self.assertTrue(Path(published.get_prod_path(), "manifest.json").is_file())

        self.assertTrue(Path(public.get_prod_path(), public.introduction).is_file())
        self.assertTrue(Path(public.get_prod_path(), public.conclusion).is_file())

        self.assertEqual(len(public.children), 2)
        for child in public.children:
            self.assertTrue(os.path.isfile(child.get_prod_path()))  # an HTML file for each chapter
            self.assertIsNone(child.introduction)
            self.assertIsNone(child.conclusion)

    def test_publish_content_big_tuto(self):
        # 4. Big tutorial:
        bigtuto = PublishableContentFactory(type="TUTORIAL")

        bigtuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=bigtuto.gallery, user=self.user_author, mode="W")
        bigtuto.licence = self.licence
        bigtuto.save()

        # populate with 2 part (1 chapter with 1 extract each)
        bigtuto_draft = bigtuto.load_version()
        part1 = ContainerFactory(parent=bigtuto_draft, db_object=bigtuto)
        chapter1 = ContainerFactory(parent=part1, db_object=bigtuto)
        ExtractFactory(container=chapter1, db_object=bigtuto)
        part2 = ContainerFactory(parent=bigtuto_draft, db_object=bigtuto)
        chapter2 = ContainerFactory(parent=part2, db_object=bigtuto)
        ExtractFactory(container=chapter2, db_object=bigtuto)

        # publish it
        bigtuto = PublishableContent.objects.get(pk=bigtuto.pk)
        published = publish_content(bigtuto, bigtuto_draft)

        self.assertEqual(published.content, bigtuto)
        self.assertEqual(published.content_pk, bigtuto.pk)
        self.assertEqual(published.content_type, bigtuto.type)
        self.assertEqual(published.content_public_slug, bigtuto_draft.slug)
        self.assertEqual(published.sha_public, bigtuto.sha_draft)

        public = bigtuto.load_version(sha=published.sha_public, public=published)
        self.assertIsNotNone(public)
        self.assertTrue(public.PUBLIC)  # it's a PublicContent object
        self.assertEqual(public.type, published.content_type)
        self.assertEqual(public.current_version, published.sha_public)

        # test creation of files:
        self.assertTrue(os.path.isdir(published.get_prod_path()))
        self.assertTrue(os.path.isfile(os.path.join(published.get_prod_path(), "manifest.json")))

        self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), public.introduction)))
        self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), public.conclusion)))

        self.assertEqual(len(public.children), 2)
        for part in public.children:
            self.assertTrue(os.path.isdir(part.get_prod_path()))  # a directory for each part
            # ... and an HTML file for introduction and conclusion
            self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), part.introduction)))
            self.assertTrue(os.path.isfile(os.path.join(public.get_prod_path(), part.conclusion)))

            self.assertEqual(len(part.children), 1)

            for chapter in part.children:
                # the HTML file is located in the good directory:
                self.assertEqual(part.get_prod_path(), os.path.dirname(chapter.get_prod_path()))
                self.assertTrue(os.path.isfile(chapter.get_prod_path()))  # an HTML file for each chapter
                self.assertIsNone(chapter.introduction)
                self.assertIsNone(chapter.conclusion)

    def test_tagged_tree_extract(self):
        midsize = PublishableContentFactory(author_list=[self.user_author])
        midsize_draft = midsize.load_version()
        first_container = ContainerFactory(parent=midsize_draft, db_object=midsize)
        second_container = ContainerFactory(parent=midsize_draft, db_object=midsize)
        first_extract = ExtractFactory(container=first_container, db_object=midsize)
        second_extract = ExtractFactory(container=second_container, db_object=midsize)
        tagged_tree = get_target_tagged_tree_for_extract(first_extract, midsize_draft)
        paths = {i[0]: i[3] for i in tagged_tree}
        self.assertTrue(paths[second_extract.get_full_slug()])
        self.assertFalse(paths[second_container.get_path(True)])
        self.assertFalse(paths[first_container.get_path(True)])

    def test_update_manifest(self):
        opts = {}
        path_manifest1 = settings.BASE_DIR / "fixtures" / "tuto" / "balise_audio" / "manifest.json"
        path_manifest2 = settings.BASE_DIR / "fixtures" / "tuto" / "balise_audio" / "manifest2.json"
        args = [str(path_manifest2)]
        shutil.copy(path_manifest1, path_manifest2)
        LicenceFactory(code="CC BY")
        call_command("upgrade_manifest_to_v2", *args, **opts)
        manifest = path_manifest2.open("r")
        json = json_handler.loads(manifest.read())

        self.assertTrue("version" in json)
        self.assertTrue("licence" in json)
        self.assertTrue("children" in json)
        self.assertEqual(len(json["children"]), 3)
        self.assertEqual(json["children"][0]["object"], "extract")
        os.unlink(args[0])
        path_manifest1 = settings.BASE_DIR / "fixtures" / "tuto" / "big_tuto_v1" / "manifest.json"
        path_manifest2 = settings.BASE_DIR / "fixtures" / "tuto" / "big_tuto_v1" / "manifest2.json"
        args = [str(path_manifest2)]
        shutil.copy(path_manifest1, path_manifest2)
        call_command("upgrade_manifest_to_v2", *args, **opts)
        manifest = path_manifest2.open("r")
        json = json_handler.loads(manifest.read())
        os.unlink(args[0])
        self.assertTrue("version" in json)
        self.assertTrue("licence" in json)
        self.assertTrue("children" in json)
        self.assertEqual(len(json["children"]), 5)
        self.assertEqual(json["children"][0]["object"], "container")
        self.assertEqual(len(json["children"][0]["children"]), 3)
        self.assertEqual(len(json["children"][0]["children"][0]["children"]), 3)
        path_manifest1 = settings.BASE_DIR / "fixtures" / "tuto" / "article_v1" / "manifest.json"
        path_manifest2 = settings.BASE_DIR / "fixtures" / "tuto" / "article_v1" / "manifest2.json"
        args = [path_manifest2]
        shutil.copy(path_manifest1, path_manifest2)
        call_command("upgrade_manifest_to_v2", *args, **opts)
        manifest = path_manifest2.open("r")
        json = json_handler.loads(manifest.read())

        self.assertTrue("version" in json)
        self.assertTrue("licence" in json)
        self.assertTrue("children" in json)
        self.assertEqual(len(json["children"]), 1)
        os.unlink(args[0])

    def test_generate_markdown(self):
        tuto = PublishedContentFactory(type="TUTORIAL")  # generate and publish a tutorial
        published = PublishedContent.objects.get(content_pk=tuto.pk)

        tuto2 = PublishedContentFactory(type="TUTORIAL")  # generate and publish a second tutorial
        published2 = PublishedContent.objects.get(content_pk=tuto2.pk)

        self.assertTrue(published.has_md())
        self.assertTrue(published2.has_md())
        os.remove(str(Path(published.get_extra_contents_directory(), published.content_public_slug + ".md")))
        os.remove(str(Path(published2.get_extra_contents_directory(), published2.content_public_slug + ".md")))
        self.assertFalse(published.has_md())
        self.assertFalse(published2.has_md())
        # test command with param
        call_command("generate_markdown", published.content.pk)
        self.assertTrue(published.has_md())
        self.assertFalse(published2.has_md())
        os.remove(str(Path(published.get_extra_contents_directory(), published.content_public_slug + ".md")))
        # test command without param
        call_command("generate_markdown")
        self.assertTrue(published.has_md())
        self.assertTrue(published2.has_md())

    def test_generate_pdf(self):
        """ensure the behavior of the `python manage.py generate_pdf` commmand"""

        tuto = PublishedContentFactory(type="TUTORIAL")  # generate and publish a tutorial
        published = PublishedContent.objects.get(content_pk=tuto.pk)

        tuto2 = PublishedContentFactory(type="TUTORIAL")  # generate and publish a second tutorial
        published2 = PublishedContent.objects.get(content_pk=tuto2.pk)

        # ensure that PDF exists in the first place
        self.assertTrue(published.has_pdf())
        self.assertTrue(published2.has_pdf())

        pdf_path = os.path.join(published.get_extra_contents_directory(), published.content_public_slug + ".pdf")
        pdf_path2 = os.path.join(published2.get_extra_contents_directory(), published2.content_public_slug + ".pdf")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(os.path.exists(pdf_path2))

        # 1. re-generate (all) PDFs
        os.remove(pdf_path)
        os.remove(pdf_path2)
        self.assertFalse(os.path.exists(pdf_path))
        self.assertFalse(os.path.exists(pdf_path2))
        call_command("generate_pdf")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(os.path.exists(pdf_path2))  # both PDFs are generated

        # 2. re-generate a given PDF
        os.remove(pdf_path)
        os.remove(pdf_path2)
        self.assertFalse(os.path.exists(pdf_path))
        self.assertFalse(os.path.exists(pdf_path2))
        call_command("generate_pdf", f"id={tuto.pk}")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertFalse(os.path.exists(pdf_path2))  # only the first PDF is generated

        # 3. re-generate a given PDF with a wrong id
        os.remove(pdf_path)
        self.assertFalse(os.path.exists(pdf_path))
        self.assertFalse(os.path.exists(pdf_path2))
        call_command("generate_pdf", "id=-1")  # There is no content with pk=-1
        self.assertFalse(os.path.exists(pdf_path))
        self.assertFalse(os.path.exists(pdf_path2))  # so no PDF is generated !

    def test_last_participation_is_old(self):
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        new_user = ProfileFactory().user
        reac = ContentReaction(author=self.user_author, position=1, related_content=article)
        reac.update_content("I will find you.")
        reac.save()
        article.last_note = reac
        article.save()

        self.assertFalse(last_participation_is_old(article, new_user))
        ContentRead(user=self.user_author, note=reac, content=article).save()
        reac = ContentReaction(author=new_user, position=2, related_content=article)
        reac.update_content("I will find you.")
        reac.save()
        article.last_note = reac
        article.save()
        ContentRead(user=new_user, note=reac, content=article).save()
        self.assertFalse(last_participation_is_old(article, new_user))
        self.assertTrue(last_participation_is_old(article, self.user_author))

    def testParseBadManifest(self):
        base_content = PublishableContentFactory(author_list=[self.user_author])
        versioned = base_content.load_version()
        versioned.add_container(Container("un peu plus près de 42"))
        versioned.dump_json()
        manifest = os.path.join(versioned.get_path(), "manifest.json")
        dictionary = json_handler.load(open(manifest))

        old_title = dictionary["title"]

        # first bad title
        dictionary["title"] = 81 * ["a"]
        self.assertRaises(
            BadManifestError,
            get_content_from_json,
            dictionary,
            None,
            "",
            max_title_len=PublishableContent._meta.get_field("title").max_length,
        )
        dictionary["title"] = "".join(dictionary["title"])
        self.assertRaises(
            BadManifestError,
            get_content_from_json,
            dictionary,
            None,
            "",
            max_title_len=PublishableContent._meta.get_field("title").max_length,
        )
        dictionary["title"] = "..."
        self.assertRaises(
            InvalidSlugError,
            get_content_from_json,
            dictionary,
            None,
            "",
            max_title_len=PublishableContent._meta.get_field("title").max_length,
        )

        dictionary["title"] = old_title
        dictionary["children"][0]["title"] = 81 * ["a"]
        self.assertRaises(
            BadManifestError,
            get_content_from_json,
            dictionary,
            None,
            "",
            max_title_len=PublishableContent._meta.get_field("title").max_length,
        )

        dictionary["children"][0]["title"] = "bla"
        dictionary["children"][0]["slug"] = "..."
        self.assertRaises(
            InvalidSlugError,
            get_content_from_json,
            dictionary,
            None,
            "",
            max_title_len=PublishableContent._meta.get_field("title").max_length,
        )

    def test_get_commit_author(self):
        """Ensure the behavior of `get_commit_author()` :
          - `git.Actor` use the pk of the bot account when no one is connected
          - `git.Actor` use the pk (and the email) of the connected account when available

        (Implementation of `git.Actor` is there :
        https://github.com/gitpython-developers/GitPython/blob/master/git/util.py#L312)
        """

        # 1. With user connected
        self.client.force_login(self.user_author)

        # go to whatever page, if not, `get_current_user()` does not work at all
        result = self.client.get(reverse("pages-index"))
        self.assertEqual(result.status_code, 200)

        actor = get_commit_author()
        self.assertEqual(actor["committer"].name, str(self.user_author.pk))
        self.assertEqual(actor["author"].name, str(self.user_author.pk))
        self.assertEqual(actor["committer"].email, self.user_author.email)
        self.assertEqual(actor["author"].email, self.user_author.email)

    def test_get_commit_author_not_auth(self):
        result = self.client.get(reverse("pages-index"))
        self.assertEqual(result.status_code, 200)

        actor = get_commit_author()
        self.assertEqual(actor["committer"].name, str(self.mas.pk))
        self.assertEqual(actor["author"].name, str(self.mas.pk))

    def invalid_slug_is_invalid(self):
        """ensure that an exception is raised when it should"""

        # exception are raised when title are invalid
        invalid_titles = ["-", "_", "__", "-_-", "$", "@", "&", "{}", "    ", "..."]

        for t in invalid_titles:
            self.assertRaises(InvalidSlugError, slugify_raise_on_invalid, t)

        # Those slugs are recognized as wrong slug
        invalid_slugs = [
            "",  # empty
            "----",  # empty
            "___",  # empty
            "-_-",  # empty (!)
            "&;",  # invalid characters
            "!{",  # invalid characters
            "@",  # invalid character
            "a ",  # space !
        ]

        for s in invalid_slugs:
            self.assertFalse(check_slug(s))

        # too long slugs are forbidden :
        too_damn_long_slug = "a" * (self.overridden_zds_app["content"]["maximum_slug_size"] + 1)
        self.assertFalse(check_slug(too_damn_long_slug))

    def test_adjust_char_count(self):
        """Test the `adjust_char_count` command"""

        article = PublishedContentFactory(type="ARTICLE", author_list=[self.user_author])
        published = PublishedContent.objects.filter(content=article).first()
        published.char_count = None
        published.save()

        call_command("adjust_char_count")

        published = PublishedContent.objects.get(pk=published.pk)
        self.assertEqual(published.char_count, published.get_char_count())

    def test_image_with_non_ascii_chars(self):
        """seen on #4144"""
        article = PublishableContentFactory(type="article", author_list=[self.user_author])
        image_string = (
            "![Portrait de Richard Stallman en 2014. [Source](https://commons.wikimedia.org/wiki/"
            "File:Richard_Stallman_-_Fête_de_l%27Humanité_2014_-_010.jpg).]"
            "(/media/galleries/4410/c1016bf1-a1de-48a1-9ef1-144308e8725d.jpg)"
        )
        article.sha_draft = article.load_version().repo_update(article.title, image_string, "", update_slug=False)
        article.save()
        publish_content(article, article.load_version())
        self.assertTrue(PublishedContent.objects.filter(content_id=article.pk).exists())

    def test_no_alert_on_unpublish(self):
        """related to #4860"""
        published = PublishedContentFactory(type="OPINION", author_list=[self.user_author])
        reaction = ContentReactionFactory(
            related_content=published, author=ProfileFactory().user, position=1, pubdate=datetime.datetime.now()
        )
        alert = Alert.objects.create(
            scope="CONTENT",
            comment=reaction,
            text="a text",
            author=ProfileFactory().user,
            pubdate=datetime.datetime.now(),
            content=published,
        )
        staff = StaffProfileFactory().user
        self.assertEqual(1, get_header_notifications(staff)["alerts"]["total"])
        unpublish_content(published, staff)
        self.assertEqual(0, get_header_notifications(staff)["alerts"]["total"])

        # Try to solve the alert anyway (related to #6478):
        self.client.force_login(self.staff)
        result = self.client.post(
            reverse("content:resolve-content", kwargs={"pk": published.pk}),
            {"alert_pk": alert.pk, "text": "Anéfé!"},
            follow=False,
        )
        self.assertEqual(result.status_code, 404)

    def tearDown(self):
        super().tearDown()
        PublicatorRegistry.registry = self.old_registry


@override_for_contents()
class UtilsExportOnlyReadyToPublishTests(TutorialTestMixin, TestCase):
    """
    Test exported contents contain only ready_to_publish==True parts.
    These tests can be seen as producing a 100% coverage of the template file
    templates/tutorialv2/export/content.md.
    """

    def setUp(self):
        self.licence = LicenceFactory()
        self.user_author = ProfileFactory().user

        self.old_registry = {key: value for key, value in PublicatorRegistry.get_all_registered()}

    def get_latex_file_path(self, published: PublishedContent):
        """
        Returns the LaTeX file path of a published content.
        TODO: factorize this method with what is done in zds.tutorialv2.publication_utils.publish_content()
        """
        tmp_path = os.path.join(
            settings.ZDS_APP["content"]["repo_public_path"], published.content_public_slug + "__building"
        )
        build_extra_contents_path = os.path.join(tmp_path, settings.ZDS_APP["content"]["extra_contents_dirname"])
        base_name = os.path.join(build_extra_contents_path, published.content_public_slug)
        return base_name + ".tex"

    def create_content(self):
        """
        Returns a content and its draft used in following tests.
        """
        tuto = PublishableContentFactory(type="TUTORIAL", intro="Intro tuto", conclusion="Conclusion tuto")
        tuto.authors.add(self.user_author)
        UserGalleryFactory(gallery=tuto.gallery, user=self.user_author, mode="W")
        tuto.licence = self.licence
        tuto.save()

        tuto_draft = tuto.load_version()

        return tuto, tuto_draft

    def test_mini_tuto(self):
        """
        Test everything in a mini tuto is exported:

        + Content
            + Extract
            + Extract
        """

        def check(path):
            with path.open("r") as f:
                content = f.read()
                self.assertIn(mini_tuto_draft.get_introduction(), content)
                self.assertIn(extract1.title, content)
                self.assertIn(extract1.get_text(), content)
                self.assertIn(extract2.title, content)
                self.assertIn(extract2.get_text(), content)
                self.assertIn(mini_tuto_draft.get_conclusion(), content)

        mini_tuto, mini_tuto_draft = self.create_content()
        extract1 = ExtractFactory(
            container=mini_tuto_draft, db_object=mini_tuto, title="Extract 1", text_content="Content extract 1"
        )
        extract2 = ExtractFactory(
            container=mini_tuto_draft, db_object=mini_tuto, title="Extract 2", text_content="Content extract 2"
        )

        # publish it
        published = publish_content(mini_tuto, mini_tuto_draft)

        # Test Markdown content:
        self.assertTrue(published.has_md())
        check(Path(published.get_extra_contents_directory(), published.content_public_slug + ".md"))

        # PDF generation may fail, we only test the LaTeX content:
        check(Path(self.get_latex_file_path(published)))

    def test_midsize_tutorial(self):
        """
        Test everything in a midsize_tuto is exported, with respect to ready_to_publish:

        + Content
            + Part
                + Extract
                + Extract
            + Part (not ready)
                + Extract
                + Extract
        """

        def check(path):
            with path.open("r") as f:
                content = f.read()
                self.assertIn(midsize_tuto_draft.get_introduction(), content)
                self.assertIn(part1.title, content)
                self.assertIn(part1.get_introduction(), content)
                self.assertIn(extract11.title, content)
                self.assertIn(extract11.get_text(), content)
                self.assertIn(extract12.title, content)
                self.assertIn(extract12.get_text(), content)
                self.assertIn(part1.get_conclusion(), content)
                self.assertNotIn(part2.title, content)
                self.assertNotIn(part2.get_introduction(), content)
                self.assertNotIn(extract21.title, content)
                self.assertNotIn(extract21.get_text(), content)
                self.assertNotIn(extract22.title, content)
                self.assertNotIn(extract22.get_text(), content)
                self.assertNotIn(part2.get_conclusion(), content)
                self.assertIn(midsize_tuto_draft.get_conclusion(), content)

        midsize_tuto, midsize_tuto_draft = self.create_content()
        part1 = ContainerFactory(
            parent=midsize_tuto_draft,
            db_object=midsize_tuto,
            title="Part 1 ready",
            intro="Intro part 1",
            conclusion="Conclusion part 1",
        )
        extract11 = ExtractFactory(
            container=part1, db_object=midsize_tuto, title="Extract 1.1", text_content="Content 1.1"
        )
        extract12 = ExtractFactory(
            container=part1, db_object=midsize_tuto, title="Extract 1.2", text_content="Content 1.2"
        )
        part2 = ContainerFactory(
            parent=midsize_tuto_draft,
            db_object=midsize_tuto,
            title="Part 2 not ready",
            intro="Intro part 2",
            conclusion="Conclusion part 2",
        )
        part2.ready_to_publish = False
        extract21 = ExtractFactory(
            container=part2, db_object=midsize_tuto, title="Extract 2.1", text_content="Content 2.1"
        )
        extract22 = ExtractFactory(
            container=part2, db_object=midsize_tuto, title="Extract 2.2", text_content="Content 2.2"
        )

        # publish it
        published = publish_content(midsize_tuto, midsize_tuto_draft)

        # Test Markdown content:
        self.assertTrue(published.has_md())
        check(Path(published.get_extra_contents_directory(), published.content_public_slug + ".md"))

        # PDF generation may fail, we only test the LaTeX content:
        check(Path(self.get_latex_file_path(published)))

    def test_big_tutorial(self):
        """
        Test everything in a big tuto is exported, with respect to ready_to_publish:

        + Content
            + Part
                + Chapter
                    + Extract
                    + Extract
                + Chapter (not ready)
                    + Extract
                    + Extract
            + Part (not ready)
                + Chapter
                    + Extract
                    + Extract
        """

        def check(path):
            with path.open("r") as f:
                content = f.read()
                self.assertIn(big_tuto_draft.get_introduction(), content)
                self.assertIn(part1.title, content)
                self.assertIn(part1.get_introduction(), content)
                self.assertIn(chapter11.title, content)
                self.assertIn(chapter11.get_introduction(), content)
                self.assertIn(extract111.title, content)
                self.assertIn(extract111.get_text(), content)
                self.assertIn(extract112.title, content)
                self.assertIn(extract112.get_text(), content)
                self.assertIn(chapter11.get_conclusion(), content)
                self.assertNotIn(chapter12.title, content)
                self.assertNotIn(chapter12.get_introduction(), content)
                self.assertNotIn(extract121.title, content)
                self.assertNotIn(extract121.get_text(), content)
                self.assertNotIn(extract122.title, content)
                self.assertNotIn(extract122.get_text(), content)
                self.assertNotIn(chapter12.get_conclusion(), content)
                self.assertIn(part1.get_conclusion(), content)
                self.assertNotIn(part2.title, content)
                self.assertNotIn(part2.get_introduction(), content)
                self.assertNotIn(chapter21.title, content)
                self.assertNotIn(chapter21.get_introduction(), content)
                self.assertNotIn(extract211.title, content)
                self.assertNotIn(extract211.get_text(), content)
                self.assertNotIn(extract212.title, content)
                self.assertNotIn(extract212.get_text(), content)
                self.assertNotIn(chapter21.get_conclusion(), content)
                self.assertNotIn(part2.get_conclusion(), content)
                self.assertIn(big_tuto_draft.get_conclusion(), content)

        big_tuto, big_tuto_draft = self.create_content()
        part1 = ContainerFactory(
            parent=big_tuto_draft,
            db_object=big_tuto,
            title="Part 1 partially ready",
            intro="Intro part 1",
            conclusion="Conclusion part 1",
        )
        chapter11 = ContainerFactory(
            parent=part1,
            db_object=big_tuto,
            title="Chapter 1.1 ready",
            intro="Intro chapter 1.1",
            conclusion="Conclusion chapter 1.1",
        )
        extract111 = ExtractFactory(
            container=chapter11, db_object=big_tuto, title="Extract 1.1.1", text_content="Content 1.1.1"
        )
        extract112 = ExtractFactory(
            container=chapter11, db_object=big_tuto, title="Extract 1.1.2", text_content="Content 1.1.2"
        )
        chapter12 = ContainerFactory(
            parent=part1,
            db_object=big_tuto,
            title="Chapter 1.2 not ready",
            intro="Intro chapter 1.2",
            conclusion="Conclusion chapter 1.2",
        )
        chapter12.ready_to_publish = False
        extract121 = ExtractFactory(
            container=chapter12, db_object=big_tuto, title="Extract 1.2.1", text_content="Content 1.2.1"
        )
        extract122 = ExtractFactory(
            container=chapter12, db_object=big_tuto, title="Extract 1.2.2", text_content="Content 1.2.2"
        )
        part2 = ContainerFactory(
            parent=big_tuto_draft,
            db_object=big_tuto,
            title="Part 2 not ready",
            intro="Intro part 2",
            conclusion="Conclusion part 2",
        )
        part2.ready_to_publish = False
        chapter21 = ContainerFactory(
            parent=part2,
            db_object=big_tuto,
            title="Chapter 2.1 ready",
            intro="Intro chapter 2.1",
            conclusion="Conclusion chapter 2.1",
        )
        extract211 = ExtractFactory(
            container=chapter21, db_object=big_tuto, title="Extract 2.1.1", text_content="Content 2.1.1"
        )
        extract212 = ExtractFactory(
            container=chapter21, db_object=big_tuto, title="Extract 2.1.2", text_content="Content 2.1.2"
        )

        # publish it
        published = publish_content(big_tuto, big_tuto_draft)

        # Test Markdown content:
        self.assertTrue(published.has_md())
        check(Path(published.get_extra_contents_directory(), published.content_public_slug + ".md"))

        # PDF generation may fail, we only test the LaTeX content:
        check(Path(self.get_latex_file_path(published)))

    def tearDown(self):
        super().tearDown()
        PublicatorRegistry.registry = self.old_registry
