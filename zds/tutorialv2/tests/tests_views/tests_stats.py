import datetime
import os
from copy import deepcopy
from random import randint, uniform, shuffle

import mock
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory
from zds.tutorialv2.models.database import Validation, PublishedContent
from zds.tutorialv2.tests import TutorialTestMixin

BASE_DIR = settings.BASE_DIR

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')
overridden_zds_app['content']['extra_content_generation_policy'] = 'SYNC'


class MockGAService():
    def __init__(self):
        self.graphs_data_report = None
        self.table_data_report = None
        self.referrer_report = None
        self.keyword_report = None

    def reports(self):
        return self

    def batchGet(self, body):
        report_requests = body['reportRequests']
        self.graphs_data_report = report_requests[0]
        self.table_data_report = report_requests[1]
        self.referrer_report = report_requests[2]
        self.keyword_report = report_requests[3]

        return self

    def get_metric_headers(self, metrics):
        response = []
        for metric in metrics:
            if 'time' in metric['expression'].lower():
                h_type = 'TIME'
            else:
                h_type = 'INTEGER'

            response.append({
                'name': metric['expression'],
                'type': h_type
            })
        return response

    def get_metric_values(self, metrics):
        response = []
        for metric in metrics:
            if 'time' in metric['expression'].lower():
                response.append(uniform(0, 100))
            else:
                response.append(randint(0, 100))
        return response

    def init_empty_metrics(self, metrics):
        empty = []
        for metric in metrics:
            if 'time' in metric['expression'].lower():
                empty.append(0.0)
            else:
                empty.append(0)
        return empty

    def get_total(self, rows, metrics):
        total = self.init_empty_metrics(metrics)
        for row in rows:
            total = [x + y for x, y in zip(total, row['metrics'][0]['values'])]
        return total

    def get_minimum(self, rows, metrics):
        minimum = self.init_empty_metrics(metrics)
        for row in rows:
            minimum = [min(x, y) for x, y in zip(minimum, row['metrics'][0]['values'])]
        return minimum

    def get_maximum(self, rows, metrics):
        maximum = self.init_empty_metrics(metrics)
        for row in rows:
            maximum = [max(x, y) for x, y in zip(maximum, row['metrics'][0]['values'])]
        return maximum

    def gen_date_row(self, entry):
        rows = []
        dateRanges = entry['dateRanges']
        start_date = datetime.datetime.strptime(dateRanges['startDate'], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(dateRanges['endDate'], '%Y-%m-%d')
        delta = end_date - start_date
        for i in range(delta.days + 1):
            rows.append({
                'dimensions': [(start_date + datetime.timedelta(i)).strftime('%Y%m%d')],
                'metrics': [{
                    'values': self.get_metric_values(entry['metrics'])
                }]
            })
        return rows

    def gen_page_path_row(self, entry):
        rows = []
        paths = entry['dimensionFilterClauses'][0]['filters']
        for path in paths:
            rows.append({
                'dimensions': [path['expressions']],
                'metrics': [{
                    'values': self.get_metric_values(entry['metrics'])
                }]
            })
        return rows

    def gen_full_referrer_row(self, entry):
        ref_src=['google', 'stackoverflow.com', '(direct)', '', None]
        shuffle(ref_src)
        nb_src = randint(0, len(ref_src))
        rows = []
        for src in ref_src[:nb_src]:
            rows.append({
                'dimensions': [src],
                'metrics': [{
                    'values': [randint(0, 100)]
                }]
            })
        return rows

    def gen_keyword_row(self, entry):
        key_src=['(not set)', '(not provided)', 'apprendre', '', None]
        shuffle(key_src)
        nb_src = randint(0, len(key_src))
        rows = []
        for src in key_src[:nb_src]:
            rows.append({
                'dimensions': [src],
                'metrics': [{
                    'values': [randint(0, 100)]
                }]
            })
        return rows

    def execute(self):
        reports = []
        for entry in [self.graphs_data_report, self.table_data_report, self.referrer_report, self.keyword_report]:
            if entry['dimensions'][0]['name'] == 'ga:date':
                rows = self.gen_date_row(entry)
            elif entry['dimensions'][0]['name'] == 'ga:pagePath':
                rows = self.gen_page_path_row(entry)
            elif entry['dimensions'][0]['name'] == 'ga:fullReferrer':
                rows = self.gen_full_referrer_row(entry)
            elif entry['dimensions'][0]['name'] == 'ga:keyword':
                rows = self.gen_keyword_row(entry)
            dims = []
            for dim in entry['dimensions']:
                dims.append(dim['name'])
            reports.append({
                'columnHeader': {
                    'dimensions': dims,
                    'metricHeader': {
                        'metricHeaderEntries': self.get_metric_headers(entry['metrics'])
                    }
                },
                'data': {
                    'rows': rows,
                    'totals': [{
                        'values': self.get_total(rows, entry['metrics'])
                    }],
                    'rowCount': len(rows),
                    'minimums': [{
                        'values': self.get_minimum(rows, entry['metrics'])
                    }],
                    'maximums': [{
                        'values': self.get_maximum(rows, entry['metrics'])
                    }]
                }
            })
        return {
            'reports': reports
        }


def fake_config_ga_credentials(view):
    return MockGAService()


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class StatTests(TestCase, TutorialTestMixin):

    def setUp(self):
        self.nb_part = 1
        self.nb_chapter = 1
        self.nb_section = 1
        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.published = self.get_published_content(self.user_author, self.user_staff, self.nb_part, self.nb_chapter, self.nb_section)

    def test_access_for_anonymous(self):
        # anonymous can't access to stats
        url = reverse('content:stats-content',
                      kwargs={'pk': self.published.content_pk, 'slug': self.published.content_public_slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_access_for_guest(self):
        # guest can't access to stats
        url = reverse('content:stats-content',
                      kwargs={'pk': self.published.content_pk, 'slug': self.published.content_public_slug})
        self.client.login(username=self.user_guest.username, password='hostel77')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_access_for_author(self):
        # author can access to stats
        url = reverse('content:stats-content',
                      kwargs={'pk': self.published.content_pk, 'slug': self.published.content_public_slug})
        self.client.login(username=self.user_author.username, password='hostel77')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data['display'], 'global')
        self.assertEqual(resp.context_data['urls'][0].name, self.published.title())
        self.assertEqual(resp.context_data['urls'][0].url, self.published.content.get_absolute_url_online())
        self.assertEqual(len(resp.context_data['urls']), 3)

    def test_access_for_staff(self):
        # staff can access to stats
        url = reverse('content:stats-content',
                      kwargs={'pk': self.published.content_pk, 'slug': self.published.content_public_slug})
        self.client.login(username=self.user_staff.username, password='hostel77')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def get_response_by_date(self, start_date=None, end_date=None):
        url = reverse('content:stats-content',
                      kwargs={'pk': self.published.content_pk, 'slug': self.published.content_public_slug})
        if start_date is not None and end_date is not None:
            url += '?start_date={}&end_date={}'.format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        elif end_date is not None:
            url += '?end_date={}'.format(end_date.strftime('%Y-%m-%d'))
        elif start_date is not None:
            url += '?start_date={}'.format(start_date.strftime('%Y-%m-%d'))

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
        for k, v in resp.context_data['stats'][0]['stats'].items():
            self.assertEqual(len(v), duration + 1)
        self.assertEqual(len(resp.context_data['urls']), 1 + self.nb_part + self.nb_chapter)
        self.assertEqual(len(resp.context_data['cumulative_stats_by_url']), 1 + self.nb_part + self.nb_chapter)
        for cum_stat in resp.context_data['cumulative_stats_by_url']:
            self.assertEqual(cum_stat['pageviews'] >= 0, True)
            self.assertEqual(cum_stat['avgTimeOnPage'] >= 0, True)
            self.assertEqual(cum_stat['users'] >= 0, True)
            self.assertEqual(cum_stat['newUsers'] >= 0, True)
            self.assertEqual(cum_stat['sessions'] >= 0, True)

    @mock.patch("zds.tutorialv2.views.published.ContentStatisticsView.config_ga_credentials",
                fake_config_ga_credentials)
    def test_query_date_parameter_duration(self):
        self.client.login(username=self.user_author.username, password='hostel77')
        # By default we only have the last 7 days
        self.check_success_result_by_duration()
        self.check_success_result_by_duration(0)
        self.check_success_result_by_duration(1)
        self.check_success_result_by_duration(7)
        self.check_success_result_by_duration(30)
        self.check_success_result_by_duration(365)

    @mock.patch("zds.tutorialv2.views.published.ContentStatisticsView.config_ga_credentials",
                fake_config_ga_credentials)
    def test_query_string_parameter_duration(self):

        # By default we only have the last 7 days
        default_duration = 7
        self.client.login(username=self.user_author.username, password='hostel77')
        url = reverse('content:stats-content',
                      kwargs={'pk': self.published.content_pk, 'slug': self.published.content_public_slug})
        # If a weird value is given, we fallback on default case
        resp = self.client.get(url + '?start_date=weird')
        self.assertEqual(resp.status_code, 200)
        for k, v in resp.context_data['stats'][0]['stats'].items():
            self.assertEqual(len(v), default_duration + 1)

    @mock.patch("zds.tutorialv2.views.published.ContentStatisticsView.config_ga_credentials",
                fake_config_ga_credentials)
    def test_end_before_start_date_parameter_duration(self):
        today = datetime.datetime.today()
        before_seven_days = today - datetime.timedelta(days=7)

        self.client.login(username=self.user_author.username, password='hostel77')

        resp = self.get_response_by_date(today, before_seven_days)

        self.assertEqual(resp.status_code, 200)

    def get_published_content(self, author, user_staff, nb_part=1, nb_chapter=1, nb_extract=1):
        bigtuto = PublishableContentFactory(type='TUTORIAL')

        bigtuto.authors.add(author)
        UserGalleryFactory(gallery=bigtuto.gallery, user=author, mode='W')
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
        self.client.login(username=author, password='hostel77')

        # ask validation
        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': bigtuto.pk, 'slug': bigtuto.slug}),
            {
                'text': 'ask for validation',
                'source': '',
                'version': bigtuto_draft.current_version
            },
            follow=False)

        # login with staff and publish
        self.client.login(username=user_staff.username, password='hostel77')

        validation = Validation.objects.filter(content=bigtuto).last()

        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)

        # accept
        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': 'accept validation',
                'is_major': True,
                'source': ''
            },
            follow=False)
        self.client.logout()

        published = PublishedContent.objects.filter(content=bigtuto).first()
        self.assertIsNotNone(published)
        return published
