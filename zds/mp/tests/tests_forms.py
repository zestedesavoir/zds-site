# coding: utf-8

from django.test import TestCase

from zds.member.factories import ProfileFactory, StaffFactory
from zds.mp.forms import PrivateTopicForm, PrivatePostForm
from zds.mp.factories import PrivateTopicFactory


class PrivateTopicFormTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.staff1 = StaffFactory()

    def test_valid_topic_form(self):
        data = {
            'participants':
                self.profile1.user.username
                + ',' + self.staff1.username,
            'title': 'Test title',
            'subtitle': 'Test subtitle',
            'text': 'blabla'
        }

        form = PrivateTopicForm(data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_topic_form_user_notexist(self):

        data = {
            'participants': self.profile1.user.username + ', toto, tata',
            'title': 'Test title',
            'subtitle': 'Test subtitle',
            'text': 'blabla'
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_no_participants(self):

        data = {
            'title': 'Test title',
            'subtitle': 'Test subtitle',
            'text': 'blabla'
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_participants(self):

        data = {
            'participants': ' ',
            'title': 'Test title',
            'subtitle': 'Test subtitle',
            'text': 'blabla'
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_no_title(self):

        data = {
            'participants': self.profile1.user.username,
            'subtitle': 'Test subtitle',
            'text': 'blabla'
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_title(self):

        data = {
            'participants': self.profile1.user.username,
            'title': ' ',
            'subtitle': 'Test subtitle',
            'text': 'blabla'
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_no_text(self):

        data = {
            'participants': self.profile1.user.username,
            'title': 'Test title',
            'subtitle': 'Test subtitle',
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_text(self):

        data = {
            'participants': self.profile1.user.username,
            'title': 'Test title',
            'subtitle': 'Test subtitle',
            'text': ' '
        }

        form = PrivateTopicForm(data=data)

        self.assertFalse(form.is_valid())


class PrivatePostFormTest(TestCase):

    def setUp(self):
        self.profile = ProfileFactory()
        self.topic = PrivateTopicFactory(author=self.profile.user)

    def test_valid_form_post(self):
        data = {
            'text': 'blabla'
        }

        form = PrivatePostForm(self.topic, self.profile.user, data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_form_post_empty_text(self):
        data = {
            'text': ' '
        }

        form = PrivatePostForm(self.topic, self.profile.user, data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_form_post_no_text(self):
        form = PrivatePostForm(self.topic, self.profile.user, data={})

        self.assertFalse(form.is_valid())
