from copy import deepcopy

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

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
    TEXT_FIRST_MODIFICATION = "Modified introduction"
    TEXT_SECOND_MODIFICATION = "Modified Introduction"

    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        overridden_zds_app["content"]["default_licence_pk"] = LicenceFactory().pk

        self.user_author = ProfileFactory().user
        self.client.force_login(self.user_author)

        # Publish an article
        self.article = PublishedContentFactory(author_list=[self.user_author], type="ARTICLE")

    def _new_draft_version(self, text):
        """Create a new draft version."""
        result = self.client.post(
            reverse("content:edit-introduction", args=[self.article.pk]),
            {"introduction": text},
            follow=False,
        )
        self.assertEqual(result.status_code, 302)
        self.article.refresh_from_db()  # the previous request changes sha_draft

    def test_sidebar_items_on_public_page(self):
        def common_tests():
            public_page = self.client.get(self.article.get_absolute_url_online())

            self.assertNotContains(public_page, PublicActionsState.messages["public_is_same"])
            self.assertContains(public_page, PublicActionsState.messages["export_content"])
            self.assertNotContains(public_page, ValidationActions.messages["validation_is_same"])

            return public_page

        public_page = common_tests()
        self.assertContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_more_recent"])

        self._new_draft_version(self.TEXT_FIRST_MODIFICATION)

        public_page = common_tests()
        self.assertNotContains(public_page, self.TEXT_FIRST_MODIFICATION)
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertContains(public_page, PublicActionsState.messages["draft_is_more_recent"])

        request_validation(self.article)

        public_page = common_tests()
        self.assertNotContains(public_page, self.TEXT_FIRST_MODIFICATION)
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertContains(public_page, PublicActionsState.messages["draft_is_more_recent"])

        # Now a new draft version, to have different version from validation
        self._new_draft_version(self.TEXT_SECOND_MODIFICATION)

        public_page = common_tests()
        self.assertNotContains(public_page, self.TEXT_FIRST_MODIFICATION)
        self.assertNotContains(public_page, self.TEXT_SECOND_MODIFICATION)
        self.assertNotContains(public_page, PublicActionsState.messages["draft_is_same"])
        self.assertContains(public_page, PublicActionsState.messages["draft_is_more_recent"])

    def test_sidebar_items_on_draft_page(self):
        def common_tests():
            draft_page = self.client.get(
                reverse("content:view", args=[self.article.pk, self.article.slug]), follow=False
            )

            self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_same"])
            self.assertNotContains(draft_page, PublicActionsState.messages["draft_is_more_recent"])
            self.assertNotContains(draft_page, PublicActionsState.messages["export_content"])

            return draft_page

        draft_page = common_tests()
        self.assertContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, ValidationActions.messages["validation_is_same"])

        self._new_draft_version(self.TEXT_FIRST_MODIFICATION)

        draft_page = common_tests()
        self.assertContains(draft_page, self.TEXT_FIRST_MODIFICATION)
        self.assertNotContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, ValidationActions.messages["validation_is_same"])

        request_validation(self.article)

        draft_page = common_tests()
        self.assertContains(draft_page, self.TEXT_FIRST_MODIFICATION)
        self.assertNotContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertContains(draft_page, ValidationActions.messages["validation_is_same"])

        # Now a new draft version, to have different version from validation
        self._new_draft_version(self.TEXT_SECOND_MODIFICATION)

        draft_page = common_tests()
        self.assertContains(draft_page, self.TEXT_SECOND_MODIFICATION)
        self.assertNotContains(draft_page, self.TEXT_FIRST_MODIFICATION)
        self.assertNotContains(draft_page, PublicActionsState.messages["public_is_same"])
        self.assertNotContains(draft_page, ValidationActions.messages["validation_is_same"])

    def test_sidebar_items_on_validation_page(self):
        def common_tests():
            validation_page = self.client.get(
                reverse("content:validation-view", args=[self.article.pk, self.article.slug]), follow=False
            )

            self.assertContains(validation_page, self.TEXT_FIRST_MODIFICATION)
            self.assertNotContains(validation_page, PublicActionsState.messages["draft_is_same"])
            self.assertNotContains(validation_page, PublicActionsState.messages["public_is_same"])
            self.assertNotContains(validation_page, PublicActionsState.messages["draft_is_more_recent"])
            self.assertNotContains(validation_page, PublicActionsState.messages["export_content"])
            self.assertNotContains(validation_page, ValidationActions.messages["validation_is_same"])

            return validation_page

        self._new_draft_version(self.TEXT_FIRST_MODIFICATION)
        request_validation(self.article)

        # Now a new draft version, to have different version from validation
        self._new_draft_version(self.TEXT_SECOND_MODIFICATION)

        validation_page = common_tests()
        self.assertNotContains(validation_page, self.TEXT_SECOND_MODIFICATION)
