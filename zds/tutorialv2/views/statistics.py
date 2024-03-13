import itertools
import logging
import urllib.parse
from datetime import timedelta, datetime, date

import requests
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from zds.tutorialv2.forms import ContentCompareStatsURLForm
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin
from zds.tutorialv2.utils import NamedUrl


class StatisticsException(Exception):
    """A class to distinguish exceptions raised ourselves by our code from
    other exceptions: ours have two arguments: the logger to use and the
    message."""

    def __init__(self, logger, msg):
        super().__init__(logger, msg)


class ContentStatisticsView(SingleOnlineContentDetailViewMixin, FormView):
    template_name = "tutorialv2/stats/index.html"
    form_class = ContentCompareStatsURLForm
    urls = []
    matomo_token_auth = settings.ZDS_APP["site"]["matomo_token_auth"]
    matomo_api_url = "{}/index.php?token_auth={}".format(settings.ZDS_APP["site"]["matomo_url"], matomo_token_auth)
    matomo_site_id = settings.ZDS_APP["site"]["matomo_site_id"]
    logger = logging.getLogger(__name__)

    def post(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.get_urls_to_render()
        kwargs["urls"] = [(named_url.url, named_url.name) for named_url in self.named_urls]
        return kwargs

    def form_valid(self, form):
        self.urls = form.cleaned_data["urls"]
        return super().get(self.request)

    def get_content_urls(self):
        content = self.versioned_object
        urls = [NamedUrl(content.title, content.get_absolute_url_online(), 0)]
        if content.has_extracts():
            return urls
        for child in content.children:
            urls.append(NamedUrl(child.title, child.get_absolute_url_online(), 1))
            if not child.has_extracts():
                for subchild in child.children:
                    urls.append(NamedUrl(subchild.title, subchild.get_absolute_url_online(), 2))
        return urls

    def get_urls_to_render(self):
        all_named_urls = self.get_content_urls()
        urls = self.request.GET.getlist("urls", None) or self.urls
        if urls:
            named_urls = [named_url for named_url in all_named_urls if named_url.url in urls]
            requested_named_urls = named_urls
            if len(urls) == 1:
                display_mode = "details"
            else:
                display_mode = "comparison"
        else:
            requested_named_urls = [all_named_urls[0]]
            named_urls = all_named_urls
            display_mode = "global"

        self.requested_named_urls = requested_named_urls
        self.named_urls = named_urls
        self.display_mode = display_mode

    def get_start_and_end_dates(self):
        end_date = self.request.GET.get("end_date", None)
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except TypeError:
            end_date = date.today()
        except ValueError:
            end_date = date.today()
            messages.error(self.request, _("La date de fin fournie est invalide."))

        start_date = self.request.GET.get("start_date", None)
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except TypeError:
            start_date = end_date - timedelta(days=7)
        except ValueError:
            start_date = end_date - timedelta(days=7)
            messages.error(self.request, _("La date de début fournie est invalide."))

        if start_date > end_date:
            end_date, start_date = start_date, end_date

        return start_date, end_date

    def get_matomo_request(self, request_data):
        request_data.update(
            {
                "module": "API",
                "idSite": self.matomo_site_id,
                "language": "fr",
                "format": "JSON",
            }
        )

        # self.logger.info("Matomo request data")
        # self.logger.info(request_data)
        response = requests.post(url=self.matomo_api_url, data=request_data)
        response_data = response.json()
        # self.logger.info("Matomo response data")
        # self.logger.info(response_data)
        return response_data

    @staticmethod
    def get_graph_metrics(data, metric_name):
        x = []
        y = []
        for key, val in data.items():
            x.append(key)
            if len(val) == 0:
                y.append(0)
            else:
                y.append(val[0].get(metric_name, 0))
        return (x, y)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not (self.is_author or self.is_staff):
            raise PermissionDenied

        named_urls = self.named_urls
        requested_named_urls = self.requested_named_urls
        display_mode = self.display_mode

        start_date, end_date = self.get_start_and_end_dates()
        date_range = "{},{}".format(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        def get_request_label(named_url):
            # Generate the "label" parameter corresponding to named_url for a request
            # From: /alice-and-bob/foo-bar/
            # To: alice-and-bob > foo-bar
            return named_url.url[1:-1].replace("/", " > ")

        def get_response_label(named_url):
            # Generate the "label" corresponding to named_url in the response data
            # From: /alice-and-bob/foo-bar/
            # To: foo-bar
            return named_url.url.split("/")[-2]

        # GRAPHS
        graphs_data = {}
        for named_url in requested_named_urls:
            graphs_data[named_url] = {}
            response_data = self.get_matomo_request(
                {
                    "method": "Actions.getPageUrls",
                    "date": date_range,
                    "period": "day",
                    "label": get_request_label(named_url),
                }
            )
            for metric_name in ("avg_time_on_page", "nb_hits", "nb_visits"):
                graphs_data[named_url][metric_name] = self.get_graph_metrics(response_data, metric_name)
        # self.logger.info("Graphs data")
        # self.logger.info(graphs_data)

        # HUGE TABLE
        bulk_request_data = {"method": "API.getBulkRequest"}
        for index, named_url in enumerate(named_urls):
            individual_request_data = {
                "method": "Actions.getPageUrls",
                "idSite": self.matomo_site_id,
                "date": date_range,
                "period": "range",
                "label": get_request_label(named_url),
            }
            bulk_request_data.update({f"urls[{index}]": urllib.parse.urlencode(individual_request_data)})
        response_data = self.get_matomo_request(bulk_request_data)

        temp_data = {}
        for elem in response_data:
            try:
                temp_data[elem[0]["label"]] = {
                    "avg_time_on_page": elem[0]["avg_time_on_page"],
                    "nb_hits": elem[0]["nb_hits"],
                    "nb_visits": elem[0]["nb_visits"],
                }
            except IndexError:
                continue
        huge_table_data = {}
        for named_url in named_urls:
            try:
                huge_table_data[named_url] = temp_data[get_response_label(named_url)]
            except KeyError:
                huge_table_data[named_url] = {
                    "avg_time_on_page": 0,
                    "nb_hits": 0,
                    "nb_visits": 0,
                }
        # self.logger.info("Huge table data")
        # self.logger.info(huge_table_data)

        # SMALL TABLES
        segments = []
        for named_url in requested_named_urls:
            # TODO: Replace https://zestedesavoir.com by the adequate settings variable
            absolute_url = f"https://zestedesavoir.com{named_url.url}"
            segments.append(f"pageUrl=^{urllib.parse.quote_plus(absolute_url)}")

        bulk_request_data = {"method": "API.getBulkRequest"}
        for index, method in enumerate(["Referrers.getReferrerType", "Referrers.getWebsites", "Referrers.getKeywords"]):
            individual_request_data = {
                "method": method,
                "idSite": self.matomo_site_id,
                "date": date_range,
                "period": "range",
                "segment": ",".join(segments),
            }
            bulk_request_data.update({f"urls[{index}]": urllib.parse.urlencode(individual_request_data)})
        response_data = self.get_matomo_request(bulk_request_data)

        referrer_types = {}
        for elem in response_data[0]:
            referrer_types[elem["label"]] = elem["nb_visits"]
        # self.logger.info("Referrer types")
        # self.logger.info(referrer_types)

        referrer_websites = {}
        for elem in response_data[1]:
            referrer_websites[elem["label"]] = elem["nb_visits"]
        # self.logger.info("Referrer websites")
        # self.logger.info(referrer_websites)

        referrer_keywords = {}
        for elem in response_data[2]:
            referrer_keywords[elem["label"]] = elem["nb_visits"]
        # self.logger.info("Referrer keywords")
        # self.logger.info(referrer_keywords)

        context.update(
            {
                "urls": named_urls,
                "display": display_mode,
                "graphs_data": graphs_data,
                "huge_table_data": huge_table_data,
                "referrer_types": referrer_types,
                "referrer_websites": referrer_websites,
                "referrer_keywords": referrer_keywords,
            }
        )
        return context
