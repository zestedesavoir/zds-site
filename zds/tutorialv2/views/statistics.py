import itertools
import logging
import urllib.parse
import uuid
from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta
from json import dumps, loads
from typing import Any, List

import requests
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Subquery
from django.http import Http404, StreamingHttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView

from zds.tutorialv2.forms import ContentCompareStatsURLForm
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin
from zds.tutorialv2.models.quizz import QuizzAvailableAnswer, QuizzQuestion, QuizzUserAnswer
from zds.tutorialv2.models.versioned import VersionedContent
from zds.tutorialv2.utils import NamedUrl


class StatisticsException(Exception):
    """A class to distinguish exceptions raised ourselves by our code from
    other exceptions: ours have two arguments: the logger to use and the
    message."""

    def __init__(self, logger, msg):
        super().__init__(logger, msg)


class ContentQuizzStatistics(SingleOnlineContentFormViewMixin):
    form_class = QuizzStatsForm

    def get_form_kwargs(self):
        return {
            "json_dict": loads(self.request.body.decode("utf-8")),
        }

    def form_valid(self, form):
        url = form.cleaned_data["url"]
        answers = {k: v for k, v in form.cleaned_data["result"].items()}
        resp_id = str(uuid.uuid4())
        for question, answers in answers.items():
            db_question = QuizzQuestion.objects.filter(question=question, url=url).first()
            if not db_question:
                db_question = QuizzQuestion(question=question, url=url, question_type="qcm")
                db_question.save()
            given_available_answers = form.cleaned_data["expected"][question]
            answers_labels = list(given_available_answers.keys())
            known_labels = QuizzAvailableAnswer.objects.filter(
                related_question=db_question, label__in=answers_labels
            ).values_list("label", flat=True)

            not_existing_answers = [label for label in answers_labels if label not in known_labels]

            QuizzUserAnswer.objects.exclude(answer__in=answers_labels).filter(related_question=db_question).delete()
            QuizzAvailableAnswer.objects.exclude(label__in=answers_labels).filter(related_question=db_question).delete()

            for label in not_existing_answers:
                db_answer = QuizzAvailableAnswer(
                    related_question=db_question, label=label, is_good=given_available_answers[label]
                )
                db_answer.save()
            for answer in answers["labels"]:
                stat = QuizzUserAnswer(
                    related_content=self.object, related_question=db_question, full_answer_id=resp_id, answer=answer
                )
                stat.save()
        return StreamingHttpResponse(dumps({"status": "ok"}))


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

    def get_export_urls(self):
        content: VersionedContent = self.versioned_object
        content_type = content.type.lower()
        epub_url = reverse(f"{content_type}:download-epub", kwargs={"pk": content.pk, "slug": content.slug})
        pdf_url = reverse(f"{content_type}:download-pdf", kwargs={"pk": content.pk, "slug": content.slug})
        urls = [
            NamedUrl("epub", epub_url, 0),
            NamedUrl("pdf", pdf_url, 0),
        ]

        return urls

    def get_all_statistics(
        self, urls: list[NamedUrl], start: datetime | date, end: datetime | date, methods
    ) -> dict[str, list]:
        """Fetch statistics from Matomo in batches of at most 3 URLs per request.

        Matomo bulk API is queried with a cartesian product of `methods` and a
        chunk of `urls` (size <= 3). Results are aggregated to preserve the
        original `urls` order for each method.
        """
        date_ranges = f"{start:%Y-%m-%d},{end:%Y-%m-%d}"

        # Initialize the aggregated structure with one list per method
        data_structured = {method: [] for method in methods}

        # Process URLs in chunks of 3 to limit the bulk size per request
        # this is done to reduce matomo memory load on big tuto with many parts & chapters
        for i in range(0, len(urls), 3):
            url_chunk = urls[i : min(i + 3, len(urls))]

            # Build a fresh bulk request for this chunk
            data_request = {
                "module": "API",
                "method": "API.getBulkRequest",
                "format": "json",
                "filter_limit": -1,
            }

            self.build_matomo_payload(data_request, date_ranges, methods, url_chunk)

            # Execute the bulk request for this chunk
            response_matomo = requests.post(url=self.matomo_api_url, data=data_request)
            data = response_matomo.json()

            # Top-level error returned by Matomo
            if isinstance(data, dict) and data.get("result", "") == "error":
                raise StatisticsException(self.logger.error, data.get("message", "Unknown matomo error"))

            # Validate and aggregate each response item in the same order
            for page_index, matomo_stat_for_url_tuple in enumerate(itertools.product(methods, url_chunk)):
                if isinstance(data[page_index], dict) and data[page_index].get("result", "") == "error":
                    raise StatisticsException(
                        self.logger.error,
                        data[page_index].get("message", "Unknown matomo error for " + matomo_stat_for_url_tuple[1].url),
                    )

                method = matomo_stat_for_url_tuple[0]
                data_structured[method].append(data[page_index])

        return data_structured

    def build_matomo_payload(self, data_request: dict[str, str | int], date_ranges, methods: list[str], url_chunk):
        for index, method_url in enumerate(itertools.product(methods, url_chunk)):
            method = method_url[0]
            url = method_url[1]
            absolute_url = f"{self.request.scheme}://{self.request.get_host()}{url.url}"
            param_url = f"pageUrl=={urllib.parse.quote_plus(absolute_url)}"

            request_params = {
                "method": method,
                "idSite": self.matomo_site_id,
                "date": date_ranges,
                "period": "day",
            }
            # Referrers requests use segment to define url
            if method.startswith("Referrers"):
                request_params["segment"] = ",".join([param_url])
            elif method == "Actions.getPageUrl":
                request_params["pageUrl"] = absolute_url

            data_request.update({f"urls[{index}]": urllib.parse.urlencode(request_params)})

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

        return x, y

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

        try:
            end_date = self.request.GET.get("end_date", None) or date.today()
            end_date = datetime.strptime(str(end_date), "%Y-%m-%d").date()
        except (TypeError, ValueError) as e:
            raise Http404("Invalid end date format") from e

        try:
            start_date = self.request.GET.get("start_date", None) or (end_date - timedelta(days=7))
            start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()

        except (TypeError, ValueError) as e:
            raise Http404("Invalid start date format") from e

        return start_date, end_date

    def get_display_mode(self, urls):
        # TODO make display_mode an enum ?
        # Good idea, but not straightforward for the template integration
        if len(urls) == len(self.get_content_urls()):
            return "global"
        if len(urls) == 1:
            return "details"
        return "comparison"

    @staticmethod
    def get_cumulative(stats: dict[str, list]) -> dict[str, int]:
        cumul = {"total": 0}
        for info_date, infos_stat in stats.items():
            cumul["total"] += len(infos_stat)
            for info_stat in infos_stat:
                for key, val in info_stat.items():
                    if type(val) == str or isinstance(val, dict):
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
        report_fields = [("nb_uniq_visitors", False), ("nb_hits", False), ("avg_time_on_page", True)]
        export_urls = self.get_export_urls()

        try:
            all_statistics = self.get_all_statistics(
                urls,
                start_date,
                end_date,
                ["Referrers.getReferrerType", "Referrers.getWebsites", "Referrers.getKeywords", "Actions.getPageUrl"],
            )
            export_statistics = self.get_all_statistics(export_urls, start_date, end_date, ["Actions.getPageUrl"])
        except StatisticsException as e:
            all_statistics = {}
            export_statistics = {}
            logger_method, msg = e.args
            logger_method(f"Something failed with Matomo reporting system: {msg}")
            messages.error(self.request, _("Impossible de récupérer les statistiques du site ({}).").format(msg))
        except Exception as e:
            all_statistics = {}
            export_statistics = {}
            self.logger.error(f"Something failed with Matomo reporting system: {e}")
            messages.error(self.request, _("Impossible de récupérer les statistiques du site ({}).").format(e))

        result_report = {}
        if all_statistics:
            all_stats = all_statistics["Actions.getPageUrl"]
            all_ref_websites = all_statistics["Referrers.getWebsites"]
            all_ref_types = all_statistics["Referrers.getReferrerType"]
            all_ref_keyword = all_statistics["Referrers.getKeywords"]

            for index, url in enumerate(urls):
                grand_totals = ContentStatisticsView.get_cumulative(all_stats[index])
                reports[url] = {}
                cumulative_stats[url] = {}

                self.__format_result(all_stats, grand_totals, cumulative_stats, index, report_fields, reports, url)

                referrers = self.merge_ref_to_data(referrers, self.get_ref_metrics(all_ref_websites[index]))
                type_referrers = self.merge_ref_to_data(type_referrers, self.get_ref_metrics(all_ref_types[index]))
                keywords = self.merge_ref_to_data(keywords, self.get_ref_metrics(all_ref_keyword[index]))

            if display_mode.lower() == "global":
                """
                {
                  "global": {
                        "nb_uniq_visitors": (
                            ["2025-11-06", "2025-11-07", "2025-11-08"],
                            [2500, 2800, 2650] ),
                        "nb_hits": (
                            ["2025-11-06", "2025-11-07", "2025-11-08"],
                            [8500, 9200, 8900]  # Somme de tous les hits pour toutes les URLs
                        ),
                        "avg_time_on_page": (
                            ["2025-11-06", "2025-11-07", "2025-11-08"],
                            [480, 520, 505]  # Somme des temps moyens (pas vraiment une moyenne au final)
                        )
                  },
                  "epub": {
                    ...
                  },
                  "pdf": {
                    ...
                  }
                }
                """
                result_report = {NamedUrl(display_mode, "", 0): self.merge_report_to_global(reports, report_fields)}
                export_reports = {}
                export_cumulative_stats = {}
                self.__format_export_report(
                    export_cumulative_stats, export_reports, export_statistics, export_urls, report_fields
                )
                result_report.update(export_reports)
            else:
                result_report = reports
        quizz_stats = self.build_quizz_stats(end_date, start_date)
        context.update(
            {
                "display": display_mode,
                "urls": urls,
                "reports": result_report,
                "cumulative_stats": cumulative_stats,
                "referrers": referrers,
                "type_referrers": type_referrers,
                "keywords": keywords,
                "quizz": quizz_stats,
            }
        )
        return context

    def __format_export_report(
        self,
        export_cumulative_stats: dict[Any, Any],
        export_reports: dict[Any, Any],
        export_statistics: dict[str, list] | dict[Any, Any],
        export_urls: list[NamedUrl],
        report_fields: list[tuple[str, bool]],
    ):
        for export_index, export_url in enumerate(export_urls):
            export_grand_totals = ContentStatisticsView.get_cumulative(
                export_statistics["Actions.getPageUrl"][export_index]
            )
            export_reports[export_url] = {}
            export_cumulative_stats[export_url] = {}
            self.__format_result(
                export_statistics["Actions.getPageUrl"],
                export_grand_totals,
                export_cumulative_stats,
                export_index,
                report_fields,
                export_reports,
                export_url,
            )

    def __format_result(
        self,
        all_stats: list,
        grand_totals: dict[str, int],
        cumulative_stats: dict,
        index: int,
        report_field: list[tuple[str, bool]],
        reports: dict,
        url: NamedUrl,
    ):
        for field_name, is_avg in report_field:
            reports[url][field_name] = ContentStatisticsView.get_stat_metrics(all_stats[index], field_name)
            if is_avg:
                cumulative_stats[url][field_name] = 0
                if grand_totals.get("total") > 0:
                    cumulative_stats[url][field_name] = grand_totals.get(field_name, 0) / grand_totals.get("total")
            else:
                cumulative_stats[url][field_name] = grand_totals.get(field_name, 0)

    def build_quizz_stats(self, end_date, start_date):
        quizz_stats = {}
        base_questions = list(
            QuizzUserAnswer.objects.filter(
                date_answer__range=(start_date, end_date), related_content__pk=self.object.pk
            ).values_list("related_question", flat=True)
        )
        total_per_question = list(
            QuizzUserAnswer.objects.values("related_question__pk", "full_answer_id")
            .filter(related_question__pk__in=base_questions, date_answer__range=(start_date, end_date))
            .annotate(nb=Count("full_answer_id"))
        )
        total_per_question = Counter([a["related_question__pk"] for a in total_per_question])
        total_per_label = list(
            QuizzUserAnswer.objects.values(
                "related_question__pk", "related_question__question", "related_question__url", "answer"
            )
            .filter(related_question__in=base_questions, date_answer__range=(start_date, end_date))
            .annotate(nb=Count("answer"))
        )
        for base_question in set(base_questions):
            full_answers_total = {}
            name = ""
            question = ""
            for available_answer in (
                QuizzAvailableAnswer.objects.filter(related_question__pk=base_question)
                .prefetch_related("related_question")
                .all()
            ):
                full_answers_total[available_answer.label] = {"good": available_answer.is_good, "nb": 0}
                name = available_answer.related_question.url
                question = available_answer.related_question.question
                for r in total_per_label:
                    if (
                        r["related_question__pk"] == base_question
                        and r["answer"].strip() == available_answer.label.strip()
                    ):
                        full_answers_total[available_answer.label]["nb"] = r["nb"]
            if name not in quizz_stats:
                quizz_stats[name] = OrderedDict()
            quizz_stats[name][question] = {"total": total_per_question[base_question], "responses": full_answers_total}
        sorted_quizz_stats = {}
        for name in sorted(quizz_stats.keys()):
            sorted_quizz_stats[name] = quizz_stats[name]
        return sorted_quizz_stats


class QuizzContentStatistics(ContentStatisticsView):
    template_name = "tutorialv2/stats/quizz_stats.html"


class DeleteQuizz(View):
    def get_start_and_end_dates(self):

        try:
            end_date = self.request.GET.get("end_date", None) or date.today()
            end_date = datetime.strptime(str(end_date), "%Y-%m-%d").date()
        except (TypeError, ValueError) as e:
            raise Http404("Invalid end date format") from e

        try:
            start_date = self.request.GET.get("start_date", None) or (end_date - timedelta(days=7))
            start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()

        except (TypeError, ValueError) as e:
            raise Http404("Invalid start date format") from e

        return start_date, end_date

    def post(self, request):

        start_date, end_date = self.get_start_and_end_dates()

        data = loads(request.body)

        # Extract the quizzName from the data
        quizz_name = data.get("quizzName")
        question = data.get("question")

        if question:
            related_question_ids = QuizzQuestion.objects.filter(url=quizz_name, question=question).values_list(
                "id", flat=True
            )
        else:
            related_question_ids = QuizzQuestion.objects.filter(url=quizz_name).values_list("id", flat=True)

        QuizzUserAnswer.objects.filter(
            related_question_id__in=Subquery(related_question_ids), date_answer__range=(start_date, end_date)
        ).delete()

        return StreamingHttpResponse(dumps({"status": "ok"}))
