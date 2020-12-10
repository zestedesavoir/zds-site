from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishedContentFactory, LicenceFactory, SubCategoryFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import override_for_contents, TutorialTestMixin


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
        self.assertEqual(self.client.login(username=self.author.user.username, password="hostel77"), True)
        result = self.client.post(
            reverse("content:edit", args=[opinion.pk, opinion.slug]),
            {
                "title": "new title",
                "description": "subtitle",
                "introduction": "introduction",
                "conclusion": "conclusion",
                "type": "OPINION",
                "licence": self.licence.pk,
                "subcategory": self.subcategory.pk,
                "last_hash": opinion.load_version().compute_hash(),
                "image": (settings.BASE_DIR / "fixtures" / "logo.png").open("rb"),
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        updated_opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertEqual("new-title", updated_opinion.slug)
        result = self.client.get(article.get_absolute_url())
        self.assertEqual(200, result.status_code)
        result = self.client.post(
            reverse("content:edit", args=[article.pk, article.slug]),
            {
                "title": "title",
                "description": "subtitle",
                "introduction": "introduction",
                "conclusion": "conclusion",
                "type": "ARTICLE",
                "licence": self.licence.pk,
                "subcategory": self.subcategory.pk,
                "last_hash": article.load_version().compute_hash(),
                "image": (settings.BASE_DIR / "fixtures" / "logo.png").open("rb"),
            },
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        result = self.client.get(article.get_absolute_url())
        self.assertEqual(200, result.status_code)
