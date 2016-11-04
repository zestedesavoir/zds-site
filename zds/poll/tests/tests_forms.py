# coding: utf-8

import datetime

from django.test import TestCase

from zds.poll.forms import PollForm, UpdatePollForm, ChoiceForm


class PollFormTest(TestCase):

    def test_valid_poll_form(self):
        data = {
            'title': 'Test poll',
            'anonymous_vote': True,
            'end_date': datetime.datetime.today() + datetime.timedelta(1),
            'multiple_vote': False,
        }
        form = PollForm(data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_poll_form_empty_title(self):
        data = {
            'title': '',
            'anonymous_vote': False,
            'end_date': datetime.datetime.today() + datetime.timedelta(5),
            'multiple_vote': True,
        }
        form = PollForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_poll_form_no_title(self):
        data = {
            'anonymous_vote': False,
            'multiple_vote': True,
        }
        form = PollForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_poll_form_bad_end_date(self):
        data = {
            'title': 'Test poll',
            'anonymous_vote': False,
            'end_date': datetime.datetime.today(),
            'multiple_vote': True,
        }
        form = PollForm(data=data)

        self.assertFalse(form.is_valid())


class UpdatePollFormTests(TestCase):

    def test_valid_update_poll_form_new_end_date(self):
        data = {
            'end_date': datetime.datetime.today() + datetime.timedelta(1),
        }
        form = UpdatePollForm(data=data)

        self.assertTrue(form.is_valid())

    def test_valid_update_poll_form_past_end_date(self):
            data = {
                'title': 'Test poll',
                'anonymous_vote': False,
                'end_date': datetime.datetime.today(),
                'multiple_vote': True,
            }
            form = UpdatePollForm(data=data)

            self.assertTrue(form.is_valid())

    def test_valid_update_poll_form_desactivate(self):
        data = {
            'activate': False,
        }
        form = UpdatePollForm(data=data)

        self.assertTrue(form.is_valid())


class ChoiceFormTests(TestCase):

    def test_valid_choice_form(self):
        data = {
            'choice': 'Test',
        }
        form = ChoiceForm(data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_choice_form_empty_choice(self):
        data = {
            'choice': '',
        }
        form = ChoiceForm(data=data)

        self.assertFalse(form.is_valid())
