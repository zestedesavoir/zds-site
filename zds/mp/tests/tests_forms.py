from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.mp.forms import PrivatePostForm, PrivateTopicForm
from zds.mp.tests.factories import PrivateTopicFactory


class PrivateTopicFormTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.staff1 = StaffProfileFactory()
        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

    def test_valid_topic_form(self):
        """Reference valid case"""
        data = {
            "participants": self.profile1.user.username + "," + self.staff1.user.username,
            "title": "Test title",
            "subtitle": "Test subtitle",
            "text": "blabla",
        }
        form = PrivateTopicForm(self.profile2.user.username, data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_topic_form_user_notexist(self):
        """Case when we write to non-existing member"""
        data = {
            "participants": self.profile2.user.username + ", toto, tata",
            "title": "Test title",
            "subtitle": "Test subtitle",
            "text": "blabla",
        }
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_no_participants(self):
        """Case when we write to no-one"""
        data = {"title": "Test title", "subtitle": "Test subtitle", "text": "blabla"}
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_participants(self):
        """Case when we write to an empty list (spaces)"""
        data = {"participants": " ", "title": "Test title", "subtitle": "Test subtitle", "text": "blabla"}
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_no_title(self):
        """Case when title is absent"""
        data = {"participants": self.profile2.user.username, "subtitle": "Test subtitle", "text": "blabla"}
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_title(self):
        """Case when title is spaces only"""
        data = {
            "participants": self.profile2.user.username,
            "title": " ",
            "subtitle": "Test subtitle",
            "text": "blabla",
        }
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_no_text(self):
        """Case when there is no text"""
        data = {
            "participants": self.profile2.user.username,
            "title": "Test title",
            "subtitle": "Test subtitle",
        }
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_text(self):
        """Case when there is no text (spaces)"""
        data = {
            "participants": self.profile2.user.username,
            "title": "Test title",
            "subtitle": "Test subtitle",
            "text": " ",
        }
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_self_message(self):
        """Case when the sender is in the receiver list"""
        data = {
            "participants": self.profile1.user.username,
            "title": "Test title",
            "subtitle": "Test subtitle",
            "text": " ",
        }
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_self_message_2(self):
        """Same as above but with case difference"""
        data = {
            "participants": self.profile1.user.username.upper(),
            "title": "Test title",
            "subtitle": "Test subtitle",
            "text": " ",
        }
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_comma(self):
        """Cas when participants is only a comma"""
        data = {"participants": ",", "title": "Test title", "subtitle": "Test subtitle", "text": "Test text"}
        form = PrivateTopicForm(self.profile1.user.username, data=data)
        self.assertFalse(form.is_valid())


class PrivatePostFormTest(TestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.topic = PrivateTopicFactory(author=self.profile.user)

    def test_valid_form_post(self):
        data = {"text": "blabla"}

        form = PrivatePostForm(self.topic, data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_post_empty_text(self):
        data = {"text": " "}

        form = PrivatePostForm(self.topic, data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_form_post_no_text(self):
        form = PrivatePostForm(self.topic, data={})
        self.assertFalse(form.is_valid())
