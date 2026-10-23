from copy import deepcopy

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import PublishableContentFactory, PublishedContentFactory
from zds.utils.models import Tag
from zds.utils.tests.factories import CategoryFactory, SubCategoryFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"
overridden_zds_app["content"]["extra_content_generation_policy"] = "NOTHING"


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "media-test")
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(SEARCH_ENABLED=False)
class ViewPublicationsTest(TutorialTestMixin, TestCase):
    """Test the library pages."""

    def setUp(self):
        self.author = ProfileFactory().user

        self.category_1 = CategoryFactory()
        self.category_2 = CategoryFactory()
        self.subcategory_1 = SubCategoryFactory(category=self.category_1)
        self.subcategory_2 = SubCategoryFactory(category=self.category_1)
        self.subcategory_3 = SubCategoryFactory(category=self.category_2)
        self.subcategory_4 = SubCategoryFactory(category=self.category_2)
        self.tag_1 = Tag.objects.create(title="random")

        # Unpublished content
        PublishableContentFactory(author_list=[self.author])

        tuto_p_1 = PublishedContentFactory(author_list=[self.author])
        tuto_p_1.subcategory.add(self.subcategory_1)
        tuto_p_1.subcategory.add(self.subcategory_2)
        self.tuto_1 = tuto_p_1.public_version

        tuto_p_2 = PublishedContentFactory(author_list=[self.author])
        tuto_p_2.subcategory.add(self.subcategory_1)
        tuto_p_2.subcategory.add(self.subcategory_2)
        self.tuto_2 = tuto_p_2.public_version

        tuto_p_3 = PublishedContentFactory(author_list=[self.author])
        tuto_p_3.subcategory.add(self.subcategory_3)
        self.tuto_3 = tuto_p_3.public_version

        article_p_1 = PublishedContentFactory(author_list=[self.author], type="ARTICLE")
        article_p_1.subcategory.add(self.subcategory_4)
        article_p_1.tags.add(self.tag_1)
        self.article_1 = article_p_1.public_version

        self.assertEqual(PublishableContent.objects.filter(type="ARTICLE").count(), 1)
        self.assertEqual(PublishableContent.objects.filter(type="TUTORIAL").count(), 4)

    def test_library_main_page(self):
        result = self.client.get(reverse("publication:list"))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(
            result.context["last_contents"], [self.article_1, self.tuto_3, self.tuto_2, self.tuto_1]
        )

    def test_category_page_1(self):
        result = self.client.get(reverse("publication:category", kwargs={"slug": self.category_1.slug}))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["last_contents"], [self.tuto_2, self.tuto_1])

    def test_category_page_2(self):
        result = self.client.get(reverse("publication:category", kwargs={"slug": self.category_2.slug}))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["last_contents"], [self.article_1, self.tuto_3])

    def test_subcategory_1(self):
        kwargs = {"slug_category": self.category_1.slug, "slug": self.subcategory_1.slug}
        result = self.client.get(reverse("publication:subcategory", kwargs=kwargs))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["last_contents"], [self.tuto_2, self.tuto_1])

    def test_subcategory_2(self):
        kwargs = {"slug_category": self.category_1.slug, "slug": self.subcategory_2.slug}
        result = self.client.get(reverse("publication:subcategory", kwargs=kwargs))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["last_contents"], [self.tuto_2, self.tuto_1])

    def test_subcategory_3(self):
        kwargs = {"slug_category": self.category_2.slug, "slug": self.subcategory_3.slug}
        result = self.client.get(reverse("publication:subcategory", kwargs=kwargs))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["last_contents"], [self.tuto_3])

    def test_subcategory_4(self):
        kwargs = {"slug_category": self.category_2.slug, "slug": self.subcategory_4.slug}
        result = self.client.get(reverse("publication:subcategory", kwargs=kwargs))
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["last_contents"], [self.article_1])

    def test_content_list_page_1(self):
        result = self.client.get(reverse("publication:list") + f"?category={self.category_1.slug}")
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["filtered_contents"], [self.tuto_2, self.tuto_1])

    def test_content_list_page_2(self):
        result = self.client.get(reverse("publication:list") + f"?category={self.category_2.slug}")
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["filtered_contents"], [self.article_1, self.tuto_3])

    def test_content_list_page_3(self):
        result = self.client.get(reverse("publication:list") + f"?subcategory={self.subcategory_1.slug}")
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["filtered_contents"], [self.tuto_2, self.tuto_1])

    def test_content_list_page_4(self):
        result = self.client.get(reverse("publication:list") + f"?subcategory={self.subcategory_3.slug}")
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["filtered_contents"], [self.tuto_3])

    def test_content_list_page_(self):
        result = self.client.get(reverse("publication:list") + f"?tag={self.tag_1.slug}")
        self.assertEqual(result.status_code, 200)
        self.assertQuerySetEqual(result.context["filtered_contents"], [self.article_1])

    def test_wrong_urls(self):
        # not existing (sub)categories and tags with slug not existing
        wrong_urls = [
            reverse("publication:list") + "?category=xxx",
            reverse("publication:list") + "?subcategory=xxx",
            reverse("publication:list") + "?tag=xxx",
            reverse("publication:category", kwargs={"slug": "xxx"}),
            reverse("publication:subcategory", kwargs={"slug_category": self.category_2.slug, "slug": "xxx"}),
            # subcategory_1 does not belong to category_2:
            reverse(
                "publication:subcategory",
                kwargs={"slug_category": self.category_2.slug, "slug": self.subcategory_1.slug},
            ),
        ]
        for url in wrong_urls:
            self.assertEqual(self.client.get(url).status_code, 404, msg=url)
