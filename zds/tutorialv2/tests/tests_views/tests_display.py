from copy import deepcopy

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import PublishedContentFactory
from zds.tutorialv2.tests.utils import request_validation
from zds.tutorialv2.views.display.config import PublicActionsState, ValidationActions
from zds.utils.tests.factories import LicenceFactory


overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"
overridden_zds_app["content"]["extra_content_generation_policy"] = "NONE"


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "media-test")
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class DisplayConfigTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        overridden_zds_app["content"]["default_licence_pk"] = LicenceFactory().pk

        self.user_author = ProfileFactory().user

    def test_sidebar_items(self):
        self.client.force_login(self.user_author)

        # Publish an article:
        article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")
        # Public page:
        public_page = self.client.get(article.get_absolute_url_online())
        self.assertContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(public_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertContains(public_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(public_page, ValidationActions.messages["validation_is_same"])
        # Draft page:
        draft_page = self.client.get(reverse("content:view", args=[article.pk, article.slug]), follow=False)
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(draft_page, ValidationActions.messages["validation_is_same"])

        # Create a new draft version:
        versioned = article.load_version()
        result = self.client.post(
            reverse("content:edit", args=[article.pk, article.slug]),
            {
                "title": article.title,
                "description": article.description,
                "introduction": "Modified introduction",
                "conclusion": "Modified conclusion",
                "type": article.type,
                "subcategory": article.subcategory.first().pk,
                "last_hash": versioned.compute_hash(),
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        article.refresh_from_db()  # the previous request changes sha_draft
        # Public page:
        public_page = self.client.get(article.get_absolute_url_online())
        self.assertNotContains(public_page, "Modified introduction")
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(public_page, PublicActionsState.messages["public_is_same"])
        self.assertContains(public_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertContains(public_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(public_page, ValidationActions.messages["validation_is_same"])
        # Draft page:
        draft_page = self.client.get(reverse("content:view", args=[article.pk, article.slug]), follow=False)
        self.assertContains(draft_page, "Modified introduction")
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertNotContains(draft_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(draft_page, ValidationActions.messages["validation_is_same"])

        # Ask validation:
        request_validation(article)
        # Public page:
        public_page = self.client.get(article.get_absolute_url_online())
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(public_page, PublicActionsState.messages["public_is_same"])
        self.assertContains(public_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertContains(public_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(public_page, ValidationActions.messages["validation_is_same"])
        # Draft page:
        draft_page = self.client.get(reverse("content:view", args=[article.pk, article.slug]), follow=False)
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertNotContains(draft_page, PublicActionsState.messages["export_content"])
        self.assertContains(draft_page, ValidationActions.messages["validation_is_same"])
        # Validation page:
        validation_page = self.client.get(
            reverse("content:validation-view", args=[article.pk, article.slug]), follow=False
        )
        self.assertNotContains(validation_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(validation_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(validation_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertNotContains(validation_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(validation_page, ValidationActions.messages["validation_is_same"])

        # Now a new draft version, to have different version from validation:
        versioned = article.load_version()
        result = self.client.post(
            reverse("content:edit", args=[article.pk, article.slug]),
            {
                "title": article.title,
                "description": article.description,
                "introduction": "Modified introduction again",
                "conclusion": "Modified conclusion",
                "type": article.type,
                "subcategory": article.subcategory.first().pk,
                "last_hash": versioned.compute_hash(),
            },
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        article.refresh_from_db()  # the previous request changes sha_draft
        # Public page:
        public_page = self.client.get(article.get_absolute_url_online())
        self.assertNotContains(public_page, "Modified introduction")
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(public_page, PublicActionsState.messages["public_is_same"])
        self.assertContains(public_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertContains(public_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(public_page, ValidationActions.messages["validation_is_same"])
        # Draft page:
        draft_page = self.client.get(reverse("content:view", args=[article.pk, article.slug]), follow=False)
        self.assertContains(draft_page, "Modified introduction")
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertNotContains(draft_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(draft_page, ValidationActions.messages["validation_is_same"])
        # Validation page:
        validation_page = self.client.get(
            reverse("content:validation-view", args=[article.pk, article.slug]), follow=False
        )
        self.assertNotContains(validation_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(validation_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(validation_page, PublicActionsState.messages["draft_is_more_recent"])
        self.assertNotContains(validation_page, PublicActionsState.messages["export_content"])
        self.assertNotContains(validation_page, ValidationActions.messages["validation_is_same"])
