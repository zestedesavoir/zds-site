from datetime import datetime, timedelta

from django.template import Context, Template
from django.test import TestCase


class DateFormatterTest(TestCase):
    # todo: Add test with localization parameters

    def setUp(self):
        now = datetime.now()
        date_previous_in_day = now - timedelta(hours=1)
        date_previous_abs = datetime(2013, 9, 12, hour=11, minute=10, second=42, microsecond=10)
        date_future_in_day = now + timedelta(hours=1)
        yearlapse = now - timedelta(days=366)

        self.context = Context(
            {
                "date_previous_in_day": date_previous_in_day,
                "date_previous_abs": date_previous_abs,
                "date_future_in_day": date_future_in_day,
                "yearlapse": yearlapse,
                "date_epoch": 42,
                "NoneVal": None,
            }
        )

    def test_format_date(self):
        # Default behaviour
        tr = Template("{% load date %}" "{{ date_previous_in_day | format_date }}").render(self.context)
        self.assertEqual("il y a une heure", tr)

        tr = Template("{% load date %}" "{{ date_future_in_day | format_date }}").render(self.context)
        self.assertEqual("Dans le futur", tr)

        tr = Template("{% load date %}" "{{ date_previous_abs | format_date }}").render(self.context)
        self.assertEqual("jeudi 12 septembre 2013 à 11h10", tr)

        # small == False :=> Same behaviour
        tr = Template("{% load date %}" "{{ date_previous_in_day | format_date:False }}").render(self.context)
        self.assertEqual("il y a une heure", tr)

        tr = Template("{% load date %}" "{{ date_future_in_day | format_date:False }}").render(self.context)
        self.assertEqual("Dans le futur", tr)

        tr = Template("{% load date %}" "{{ date_previous_abs | format_date:False }}").render(self.context)
        self.assertEqual("jeudi 12 septembre 2013 à 11h10", tr)

        # small == True :=> absolute date change
        tr = Template("{% load date %}" "{{ date_previous_in_day | format_date:True }}").render(self.context)
        self.assertEqual("il y a une heure", tr)

        tr = Template("{% load date %}" "{{ date_future_in_day | format_date:True }}").render(self.context)
        self.assertEqual("Dans le futur", tr)

        tr = Template("{% load date %}" "{{ date_previous_abs | format_date:True }}").render(self.context)
        self.assertEqual("12/09/13 à 11h10", tr)

        # Bad format
        tr = Template("{% load date %}" "{{ NoneVal | format_date }}").render(self.context)
        self.assertEqual("None", tr)

    def test_tooltip_date(self):
        # Default behaviour

        # Todo: Add test to step time less than one day with tooltip
        # Todo: I don't know how to test this without hugly hack on datetime.now()

        tr = Template("{% load date %}" "{{ date_future_in_day | tooltip_date }}").render(self.context)
        self.assertEqual("Dans le futur", tr)

        tr = Template("{% load date %}" "{{ yearlapse | tooltip_date }}").render(self.context)
        self.assertEqual("il y a 1\xa0année", tr)

        # Bad format
        tr = Template("{% load date %}" "{{ NoneVal | tooltip_date }}").render(self.context)
        self.assertEqual("None", tr)

    def test_date_from_timestamp(self):
        # Default behaviour
        tr = Template("{% load date %}" "{{ date_epoch | date_from_timestamp | format_date }}").render(self.context)

        self.assertEqual(tr, "jeudi 01 janvier 1970 à 01h00")
