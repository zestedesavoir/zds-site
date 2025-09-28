import datetime
from copy import deepcopy
from random import randint
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublishedContent, Validation
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin
from zds.tutorialv2.tests.factories import ContainerFactory, ExtractFactory, PublishableContentFactory
from zds.utils.tests.factories import LicenceFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"
overridden_zds_app["content"]["extra_content_generation_policy"] = "SYNC"


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "media-test")
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(SEARCH_ENABLED=False)
class StatTests(TestCase, TutorialTestMixin):
    def setUp(self):
        self.nb_part = 1
        self.nb_chapter = 3
        self.nb_section = 1
        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.published = self.get_published_content(
            self.user_author, self.user_staff, self.nb_part, self.nb_chapter, self.nb_section
        )

    def count_urls(self):
        cpt = 1
        if self.published.content.load_version().has_extracts():
            return 1
        for child in self.published.content.load_version().children:
            cpt += 1
            if not child.has_extracts():
                cpt += len(child.children)
        return cpt

    def _mock_response(
        self, start_date=None, end_date=None, duration=7, status=200, raise_for_status=None, count_urls=None
    ):
        methods = ["Referrers.getReferrerType", "Referrers.getWebsites", "Referrers.getKeywords", "Actions.getPageUrl"]

        if end_date is None:
            end_date = datetime.datetime.today()
        if start_date is None:
            start_date = end_date - datetime.timedelta(days=duration)

        mock_resp = mock.Mock()
        # mock raise_for_status call w/optional error
        mock_resp.raise_for_status = mock.Mock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        # set status code and content
        mock_resp.status_code = status
        # add json data if provided
        response_data = []
        if count_urls is None:
            count_urls = self.count_urls()
        for method in methods:
            for counter in range(count_urls):
                json_data = {}
                for single_date in daterange(start_date, end_date):
                    if method == "Actions.getPageUrl":
                        fuzzy_item = {
                            "label": r"\/index",
                            "nb_visits": randint(0, 1000),
                            "nb_uniq_visitors": randint(0, 1000),
                            "nb_hits": randint(0, 1000),
                            "sum_time_spent": randint(0, 1000),
                            "nb_hits_following_search": randint(0, 1000),
                            "entry_nb_uniq_visitors": randint(0, 1000),
                            "entry_nb_visits": randint(0, 1000),
                            "entry_nb_actions": randint(0, 1000),
                            "entry_sum_visit_length": randint(0, 1000),
                            "entry_bounce_count": randint(0, 1000),
                            "exit_nb_uniq_visitors": randint(0, 1000),
                            "exit_nb_visits": randint(0, 1000),
                            "avg_time_on_page": randint(0, 1000),
                            "bounce_rate": f"{randint(0, 1000)}\u00a0%",
                            "exit_rate": f"{randint(0, 1000)}\u00a0%",
                            "url": r"https:\/\/zestedesavoir.com",
                        }
                    else:
                        fuzzy_item = {
                            "label": "Reseaux sociaux",
                            "nb_uniq_visitors": randint(0, 1000),
                            "nb_visits": randint(0, 1000),
                            "nb_actions": randint(0, 1000),
                            "nb_users": randint(0, 1000),
                            "max_actions": randint(0, 1000),
                            "sum_visit_length": randint(0, 1000),
                            "bounce_count": randint(0, 1000),
                            "nb_visits_converted": randint(0, 1000),
                            "goals": {},
                            "nb_conversions": randint(0, 1000),
                            "revenue": 0,
                            "segment": "referrerType==social",
                            "referrer_type": 7,
                            "idsubdatatable": 7,
                        }
                    json_data[single_date.strftime("%Y-%m-%d")] = [fuzzy_item]
                response_data.append(json_data)
        mock_resp.json = mock.Mock(return_value=response_data)
        return mock_resp

    @mock.patch("requests.post")
    def test_access_for_anonymous(self, mock_post):
        # anonymous can't access to stats
        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        mock_post.return_value = self._mock_response()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    @mock.patch("requests.post")
    def test_access_for_guest(self, mock_post):
        # guest can't access to stats
        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        self.client.force_login(self.user_guest)
        mock_post.return_value = self._mock_response()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    @mock.patch("requests.post")
    def test_access_for_author(self, mock_post):
        # author can access to stats
        text_button_back_to_global_view = _("Revenir à la vue globale")
        text_button_compare = _("Comparer")
        text_link_details = _("(détails)")

        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        self.client.force_login(self.user_author)

        # Statistics of the global content:
        mock_post.return_value = self._mock_response()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data["display"], "global")
        self.assertEqual(resp.context_data["urls"][0].name, self.published.title())
        self.assertEqual(resp.context_data["urls"][0].url, self.published.content.get_absolute_url_online())
        self.assertEqual(len(resp.context_data["urls"]), 5)
        self.assertNotContains(resp, text_button_back_to_global_view)
        self.assertContains(resp, text_button_compare)
        self.assertContains(resp, text_link_details)
        global_urls = resp.context_data["urls"]

        # Statistics of a chapter:
        mock_post.return_value = self._mock_response(count_urls=1)
        resp = self.client.get(url + "?urls=" + global_urls[-1].url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data["display"], "details")
        self.assertEqual(len(resp.context_data["urls"]), 1)
        self.assertContains(resp, text_button_back_to_global_view)
        self.assertNotContains(resp, text_button_compare)
        self.assertNotContains(resp, text_link_details)

        # Comparison of two chapters:
        mock_post.return_value = self._mock_response(count_urls=2)
        resp = self.client.post(url, {"urls": [global_urls[-2].url, global_urls[-1].url]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data["display"], "comparison")
        self.assertEqual(len(resp.context_data["urls"]), 2)
        self.assertContains(resp, text_button_back_to_global_view)
        self.assertNotContains(resp, text_button_compare)
        self.assertContains(resp, text_link_details)

        # An opinion without extract:
        opinion = self.get_small_opinion()
        url = reverse(
            "content:stats-content",
            kwargs={"pk": opinion.content_pk, "slug": opinion.content_public_slug},
        )
        mock_post.return_value = self._mock_response(count_urls=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data["display"], "global")
        self.assertEqual(len(resp.context_data["urls"]), 1)
        self.assertNotContains(resp, text_button_back_to_global_view)
        self.assertNotContains(resp, text_button_compare)
        self.assertNotContains(resp, text_link_details)

    def test_access_for_author_matomo_error(self):
        # author can access to stats, and if request to Matomo triggers an error,
        # display the page with a message error, and not an ugly error 500 page:
        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        self.client.force_login(self.user_author)
        with self.assertLogs(level="ERROR") as error_log:
            resp = self.client.get(url)
            self.assertTrue(
                error_log.output[0].startswith(
                    "ERROR:zds.tutorialv2.views.statistics:Something failed with Matomo reporting system:"
                )
            )
        self.assertEqual(resp.status_code, 200)

    @mock.patch("requests.post")
    def test_access_for_staff(self, mock_post):
        # staff can access to stats
        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        self.client.force_login(self.user_staff)
        mock_post.return_value = self._mock_response()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def get_response_by_date(self, start_date=None, end_date=None):
        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        if start_date is not None and end_date is not None:
            url += "?start_date={}&end_date={}".format(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        elif end_date is not None:
            url += "?end_date={}".format(end_date.strftime("%Y-%m-%d"))
        elif start_date is not None:
            url += "?start_date={}".format(start_date.strftime("%Y-%m-%d"))

        resp = self.client.get(url)
        return resp

    def check_success_result_by_duration(self, duration=None):
        if duration is None:
            duration = 7
            resp = self.get_response_by_date()
        else:
            today = datetime.datetime.today()
            after_duration = today - datetime.timedelta(days=duration)
            resp = self.get_response_by_date(today, after_duration)

        self.assertEqual(resp.status_code, 200)
        for k, v in resp.context_data["reports"].items():
            for metric, date_val in v.items():
                self.assertEqual(len(date_val[0]), duration)
        self.assertEqual(len(resp.context_data["urls"]), 1 + self.nb_part + self.nb_chapter)
        self.assertEqual(len(resp.context_data["cumulative_stats"]), 1 + self.nb_part + self.nb_chapter)
        for urls, cum_stat in resp.context_data["cumulative_stats"].items():
            self.assertEqual(cum_stat["nb_hits"] >= 0, True)
            self.assertEqual(cum_stat["avg_time_on_page"] >= 0, True)
            self.assertEqual(cum_stat["nb_uniq_visitors"] >= 0, True)

    @mock.patch("requests.post")
    def test_query_date_parameter_duration(self, mock_post):
        self.client.force_login(self.user_author)
        # By default we only have the last 7 days
        mock_post.return_value = self._mock_response()
        self.check_success_result_by_duration()
        mock_post.return_value = self._mock_response(duration=0)
        self.check_success_result_by_duration(0)
        mock_post.return_value = self._mock_response(duration=1)
        self.check_success_result_by_duration(1)
        mock_post.return_value = self._mock_response(duration=7)
        self.check_success_result_by_duration(7)
        mock_post.return_value = self._mock_response(duration=30)
        self.check_success_result_by_duration(30)
        mock_post.return_value = self._mock_response(duration=365)
        self.check_success_result_by_duration(365)

    @mock.patch("requests.post")
    def test_query_string_parameter_duration(self, mock_post):
        # By default we only have the last 7 days
        default_duration = 7
        self.client.force_login(self.user_author)
        url = reverse(
            "content:stats-content",
            kwargs={"pk": self.published.content_pk, "slug": self.published.content_public_slug},
        )
        # If a weird value is given, we fallback on default case
        mock_post.return_value = self._mock_response()
        resp = self.client.get(url + "?start_date=weird")
        self.assertEqual(resp.status_code, 200)
        for k, v in resp.context_data["reports"].items():
            for metric, date_val in v.items():
                self.assertEqual(len(date_val[0]), default_duration)

    @mock.patch("requests.post")
    def test_end_before_start_date_parameter_duration(self, mock_post):
        today = datetime.datetime.today()
        before_seven_days = today - datetime.timedelta(days=7)

        self.client.force_login(self.user_author)

        mock_post.return_value = self._mock_response(start_date=before_seven_days, end_date=today)
        resp = self.get_response_by_date(today, before_seven_days)

        self.assertEqual(resp.status_code, 200)

    def get_published_content(self, author, user_staff, nb_part=1, nb_chapter=1, nb_extract=1):
        bigtuto = PublishableContentFactory(type="TUTORIAL")

        bigtuto.authors.add(author)
        UserGalleryFactory(gallery=bigtuto.gallery, user=author, mode="W")
        bigtuto.licence = LicenceFactory()
        bigtuto.save()

        # populate the bigtuto
        bigtuto_draft = bigtuto.load_version()
        for i in range(nb_part):
            part = ContainerFactory(parent=bigtuto_draft, db_object=bigtuto)
            for j in range(nb_chapter):
                chapter = ContainerFactory(parent=part, db_object=bigtuto)
                for k in range(nb_extract):
                    ExtractFactory(container=chapter, db_object=bigtuto)

        # connect with author:
        self.client.force_login(author)

        # ask validation
        self.client.post(
            reverse("validation:ask", kwargs={"pk": bigtuto.pk, "slug": bigtuto.slug}),
            {"text": "ask for validation", "source": "", "version": bigtuto_draft.current_version},
            follow=False,
        )

        # login with staff and publish
        self.client.force_login(user_staff)

        validation = Validation.objects.filter(content=bigtuto).last()

        self.client.post(
            reverse("validation:reserve", kwargs={"pk": validation.pk}), {"version": validation.version}, follow=False
        )

        # accept
        self.client.post(
            reverse("validation:accept", kwargs={"pk": validation.pk}),
            {"text": "accept validation", "is_major": True, "source": ""},
            follow=False,
        )
        self.client.logout()

        published = PublishedContent.objects.filter(content=bigtuto).first()
        self.assertIsNotNone(published)
        return published

    def get_small_opinion(self):
        """
        Returns a published opinion without extract.
        """
        opinion = PublishableContentFactory(type="OPINION")
        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode="W")
        opinion.licence = LicenceFactory()
        opinion.save()
        opinion_draft = opinion.load_version()
        return publish_content(opinion, opinion_draft)
