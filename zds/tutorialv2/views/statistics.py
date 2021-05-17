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


class ContentStatisticsView(SingleOnlineContentDetailViewMixin, FormView):
    template_name = "tutorialv2/stats/index.html"
    form_class = ContentCompareStatsURLForm
    urls = []
    matomo_token_auth = settings.ZDS_APP["site"]["matomoTokenAuth"]
    matomo_api_url = "{}/index.php?token_auth={}".format(settings.ZDS_APP["site"]["matomoUrl"], matomo_token_auth)
    matomo_site_id = settings.ZDS_APP["site"]["matomoSiteID"]
    logger = logging.getLogger(__name__)

    def post(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["urls"] = [(named_url.url, named_url.name) for named_url in self.get_urls_to_render()]
        return kwargs

    def form_valid(self, form):
        self.urls = form.cleaned_data["urls"]
        return super().get(self.request)

    def get_urls_to_render(self):
        all_named_urls = self.get_content_urls()
        base_list = self.request.GET.getlist("urls", None) or self.urls
        if base_list:
            return [named_url for named_url in all_named_urls if named_url.url in base_list]
        else:
            return all_named_urls

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

    def get_all_refs(self, url, start, end, method):
        date_ranges = "{},{}".format(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        absolute_url = f"{self.request.scheme}://{self.request.get_host()}{url.url}"
        param_url = f"pageUrl=={urllib.parse.quote_plus(absolute_url)}"

        data_request = {
            "module": "API",
            "method": method,
            "format": "json",
            "idSite": self.matomo_site_id,
            "date": date_ranges,
            "period": "day",
            "segment": ",".join([param_url]),
        }

        try:
            response_matomo = requests.post(url=self.matomo_api_url, data=data_request)
            data = response_matomo.json()
            if data.get("result", "") == "error":
                data = {}
                self.logger.error(data.get("message", "Something failed with Matomo reporting system"))
                messages.error(self.request, data.get("message", _(f"Impossible de récupérer les référents du site.")))

        except Exception:
            data = {}
            self.logger.exception(f"Something failed with Matomo reporting system")
            messages.error(self.request, _(f"Impossible de récupérer les référents du site."))

        return data

    def get_all_stats(self, url, start, end):
        date_ranges = "{},{}".format(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        absolute_url = f"{self.request.scheme}://{self.request.get_host()}{url.url}"

        data_request = {
            "module": "API",
            "method": "Actions.getPageUrl",
            "format": "json",
            "idSite": self.matomo_site_id,
            "date": date_ranges,
            "period": "day",
            "pageUrl": absolute_url,
        }

        try:
            response_matomo = requests.post(url=self.matomo_api_url, data=data_request)
            data = response_matomo.json()
            if data.get("result", "") == "error":
                data = {}
                self.logger.error(data.get("message", "Something failed with Matomo reporting system"))
                messages.error(
                    self.request, data.get("message", _(f"Impossible de récupérer les statistiques du site."))
                )
        except Exception:
            data = {}
            self.logger.exception(f"Something failed with Matomo reporting system")
            messages.error(self.request, _(f"Impossible de récupérer les statistiques du site."))

        return data

    @staticmethod
    def get_stat_metrics(data, metric_name):
        x = []
        y = []
        for key, val in data.items():
            x.append(key)
            if len(val) == 0:
                y.append(0)
            else:
                y.append(val[0].get(metric_name, 0))

        return (x, y)

    @staticmethod
    def get_ref_metrics(data):
        refs = {}
        for key, val in data.items():
            for item in val:
                if item["label"] in refs:
                    refs[item["label"]] += item["nb_visits"]
                else:
                    refs[item["label"]] = item["nb_visits"]

        return refs

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

    def get_display_mode(self, urls):
        # TODO make display_mode an enum ?
        # Good idea, but not straightforward for the template integration
        if len(urls) == 1:
            return "details"
        if len(urls) == len(self.get_content_urls()):
            return "global"
        return "comparison"

    @staticmethod
    def get_cumulative(stats):
        cumul = {"total": 0}
        for info_date, infos_stat in stats.items():
            cumul["total"] += len(infos_stat)
            for info_stat in infos_stat:
                for key, val in info_stat.items():
                    if type(val) == str:
                        continue
                    if key in cumul:
                        cumul[key] += int(val)
                    else:
                        cumul[key] = int(val)
        return cumul

    @staticmethod
    def merge_ref_to_data(metrics, refs):
        for key, item in refs.items():
            if key in metrics:
                metrics[key] += item
            else:
                metrics[key] = item
        return metrics

    @staticmethod
    def merge_report_to_global(reports, fields):
        metrics = {}
        for key, item in reports.items():
            for field, is_avg in fields:
                if field in metrics:
                    metrics[field] = (
                        metrics[field][0],
                        [i + j for (i, j) in zip(metrics[field][1], item.get(field)[1])],
                    )
                else:
                    metrics[field] = item.get(field)
        return metrics

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not (self.is_author or self.is_staff):
            raise PermissionDenied

        urls = self.get_urls_to_render()
        start_date, end_date = self.get_start_and_end_dates()
        display_mode = self.get_display_mode(urls)
        reports = {}
        cumulative_stats = {}
        referrers = {}
        type_referrers = {}
        keywords = {}
        report_field = [("nb_uniq_visitors", False), ("nb_hits", False), ("avg_time_on_page", True)]

        for url in urls:
            all_stats = self.get_all_stats(url, start_date, end_date)
            cumul_stats = self.get_cumulative(all_stats)
            all_referrers = self.get_all_refs(url, start_date, end_date, "Referrers.getWebsites")
            all_type_referrers = self.get_all_refs(url, start_date, end_date, "Referrers.getReferrerType")
            all_keywords = self.get_all_refs(url, start_date, end_date, "Referrers.getKeywords")
            reports[url] = {}
            cumulative_stats[url] = {}

            for item, is_avg in report_field:
                reports[url][item] = self.get_stat_metrics(all_stats, item)
                if is_avg:
                    cumulative_stats[url][item] = 0
                    if cumul_stats.get("total") > 0:
                        cumulative_stats[url][item] = cumul_stats.get(item, 0) / cumul_stats.get("total")
                else:
                    cumulative_stats[url][item] = cumul_stats.get(item, 0)

            referrers = self.merge_ref_to_data(referrers, self.get_ref_metrics(all_referrers))
            type_referrers = self.merge_ref_to_data(type_referrers, self.get_ref_metrics(all_type_referrers))
            keywords = self.merge_ref_to_data(keywords, self.get_ref_metrics(all_keywords))

        if display_mode.lower() == "global":
            reports = {NamedUrl(display_mode, "", 0): self.merge_report_to_global(reports, report_field)}

        context.update(
            {
                "display": display_mode,
                "urls": urls,
                "reports": reports,
                "cumulative_stats": cumulative_stats,
                "referrers": referrers,
                "type_referrers": type_referrers,
                "keywords": keywords,
            }
        )
        return context
