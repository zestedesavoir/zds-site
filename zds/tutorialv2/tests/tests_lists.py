import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory
from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContainerFactory,
    ExtractFactory,
    PublishableContentFactory,
    PublishedContentFactory,
    ValidationFactory,
)
from zds.utils.tests.factories import CategoryFactory, LicenceFactory, SubCategoryFactory


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

    def test_public_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishableContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type="ARTICLE")
        self.client.logout()

        resp = self.client.get(reverse("publication:list") + "?type=tutorial")
        self.assertContains(resp, tutorial.title)
        self.assertNotContains(resp, tutorial_unpublished.title)

        resp = self.client.get(reverse("publication:list") + "?type=article")
        self.assertContains(resp, article.title)
        self.assertNotContains(resp, article_unpublished.title)

        resp = self.client.get(reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=public")
        self.assertContains(resp, tutorial.title)
        self.assertNotContains(resp, tutorial_unpublished.title)

        resp = self.client.get(
            reverse("tutorial:find-tutorial", args=[self.user_author.username]) + "?filter=redaction"
        )
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(reverse("article:find-article", args=[self.user_author.username]) + "?filter=public")
        self.assertContains(resp, article.title)
        self.assertNotContains(resp, article_unpublished.title)

        resp = self.client.get(reverse("article:find-article", args=[self.user_author.username]) + "?filter=redaction")
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(
            reverse("article:find-article", args=[self.user_author.username]) + "?filter=chuck-norris"
        )
        self.assertEqual(resp.status_code, 404)

    def _create_and_publish_type_in_subcategory(self, content_type, subcategory):
        tuto_1 = PublishableContentFactory(type=content_type, author_list=[self.user_author])
        tuto_1.subcategory.add(subcategory)
        tuto_1.save()
        tuto_1_draft = tuto_1.load_version()
        tuto_1.public_version = publish_content(tuto_1, tuto_1_draft, is_major_update=True)
        tuto_1.save()

    def test_list_categories(self):
        category_1 = CategoryFactory()
        subcategory_1 = SubCategoryFactory(category=category_1)
        subcategory_2 = SubCategoryFactory(category=category_1)
        # Not in context if nothing published inside this subcategory
        SubCategoryFactory(category=category_1)

        for _ in range(5):
            self._create_and_publish_type_in_subcategory("TUTORIAL", subcategory_1)
            self._create_and_publish_type_in_subcategory("ARTICLE", subcategory_2)

        self.client.logout()
        resp = self.client.get(reverse("publication:list"))

        context_categories = list(resp.context_data["categories"])
        self.assertEqual(context_categories[0].contents_count, 10)
        self.assertCountEqual(context_categories[0].subcategories, [subcategory_1, subcategory_2])
        self.assertIn(category_1, context_categories)

    def test_private_lists(self):
        tutorial = PublishedContentFactory(author_list=[self.user_author])
        tutorial_unpublished = PublishableContentFactory(author_list=[self.user_author])
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        article_unpublished = PublishableContentFactory(author_list=[self.user_author], type="ARTICLE")
        self.client.force_login(self.user_author)
        resp = self.client.get(reverse("tutorial:find-tutorial", args=[self.user_author.username]))
        self.assertContains(resp, tutorial.title)
        self.assertContains(resp, tutorial_unpublished.title)
        self.assertContains(resp, "content-illu")
        resp = self.client.get(reverse("article:find-article", args=[self.user_author.username]))
        self.assertContains(resp, article.title)
        self.assertContains(resp, article_unpublished.title)
        self.assertContains(resp, "content-illu")

    def test_validation_list(self):
        """ensure the behavior of the `validation:list` page (with filters)"""

        text = "Ceci est un éléphant"

        tuto_not_reserved = PublishableContentFactory(type="TUTORIAL", author_list=[self.user_author])
        tuto_reserved = PublishableContentFactory(type="TUTORIAL", author_list=[self.user_author])
        article_not_reserved = PublishableContentFactory(type="ARTICLE", author_list=[self.user_author])
        article_reserved = PublishableContentFactory(type="ARTICLE", author_list=[self.user_author])

        all_contents = [tuto_not_reserved, tuto_reserved, article_not_reserved, article_reserved]
        reserved_contents = [tuto_reserved, article_reserved]

        # apply a filter to test category filter
        subcat = SubCategoryFactory()
        article_reserved.subcategory.add(subcat)
        article_reserved.save()

        # send in validation
        for content in all_contents:
            v = ValidationFactory(content=content, status="PENDING")
            v.date_proposition = datetime.datetime.now()
            v.version = content.sha_draft
            v.comment_authors = text

            if content in reserved_contents:
                v.validator = self.user_staff
                v.date_reserve = datetime.datetime.now()
                v.status = "PENDING_V"

            v.save()

        # first, test access for public
        result = self.client.get(reverse("validation:list"), follow=False)
        self.assertEqual(result.status_code, 302)  # get 302 → redirection to login

        # connect with author:
        self.client.force_login(self.user_author)

        result = self.client.get(reverse("validation:list"), follow=False)
        self.assertEqual(result.status_code, 403)  # get 403 not allowed

        self.client.logout()

        # connect with staff:
        self.client.force_login(self.user_staff)

        response = self.client.get(reverse("validation:list"), follow=False)
        self.assertEqual(response.status_code, 200)  # OK

        validations = response.context["validations"]
        self.assertEqual(len(validations), 4)  # a total of 4 contents in validation

        # test filters
        response = self.client.get(reverse("validation:list") + "?type=article", follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context["validations"]
        self.assertEqual(len(validations), 2)  # 2 articles

        response = self.client.get(reverse("validation:list") + "?type=tuto", follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context["validations"]
        self.assertEqual(len(validations), 2)  # 2 articles

        response = self.client.get(reverse("validation:list") + "?type=orphan", follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context["validations"]
        self.assertEqual(len(validations), 2)  # 2 not-reserved content

        for validation in validations:
            self.assertFalse(validation.content in reserved_contents)

        response = self.client.get(reverse("validation:list") + "?type=reserved", follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context["validations"]
        self.assertEqual(len(validations), 2)  # 2 reserved content

        for validation in validations:
            self.assertTrue(validation.content in reserved_contents)

        response = self.client.get(reverse("validation:list") + f"?subcategory={subcat.pk}", follow=False)
        self.assertEqual(response.status_code, 200)  # OK
        validations = response.context["validations"]
        self.assertEqual(len(validations), 1)  # 1 content with this category

        self.assertEqual(validations[0].content, article_reserved)  # the right content
