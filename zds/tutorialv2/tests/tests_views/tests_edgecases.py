from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishedContentFactory
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


@override_for_contents()
class ContentTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.author = ProfileFactory()
        self.staff = StaffProfileFactory()
        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

    def test_no_bad_slug_renaming_on_rename(self):
        """
        this test embodies the #5320 issue (first case simple workflow):

        - create an opinion with title "title"
        - create an article with the same title => it gets "-1" slug
        - rename opinion
        - make any update to article
        - try to access article
        """
        opinion = PublishedContentFactory(
            type="OPINION", title="title", author_list=[self.author.user], licence=self.licence
        )
        article = PublishedContentFactory(
            type="ARTICLE", title="title", author_list=[self.author.user], licence=self.licence
        )
        # login with author
        self.client.force_login(self.author.user)
        result = self.client.post(
            reverse("content:edit-title", args=[opinion.pk]),
            {"title": "new title"},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        updated_opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertEqual("new-title", updated_opinion.slug)
        result = self.client.get(article.get_absolute_url())
        self.assertEqual(200, result.status_code)
        result = self.client.post(
            reverse("content:edit-title", args=[article.pk]),
            {"title": "title"},
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        result = self.client.get(article.get_absolute_url())
        self.assertEqual(200, result.status_code)

    def test_default_content_type_is_tutorial(self):
        """
        Test that if a wrong content type is provided to the create-content view, TUTORIAL is used as a default
        """
        self.client.force_login(self.author.user)
        result = self.client.get(reverse("content:create-content", kwargs={"created_content_type": "WRONG_TYPE"}))
        self.assertEqual("TUTORIAL", result.context_data.get("form").initial.get("type"))
