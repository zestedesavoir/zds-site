from django.conf import settings
from django.test import TestCase

from zds.forum.forms import PostForm, TopicForm
from zds.forum.tests.factories import create_category_and_forum, create_topic_in_forum
from zds.member.tests.factories import ProfileFactory

text_too_long = (settings.ZDS_APP["forum"]["max_post_length"] + 1) * "a"


class TopicFormTest(TestCase):
    def test_valid_topic_form(self):
        data = {
            "title": "Test Topic Title",
            "subtitle": "Test Topic Subtitle",
            "tags": "test,topic,tags",
            "text": "Test Topic Text",
        }
        form = TopicForm(data=data)

        self.assertTrue(form.is_valid())

    def test_valid_topic_form_empty_tags(self):
        data = {"title": "Test Topic Title", "subtitle": "Test Topic Subtitle", "tags": "", "text": "Test Topic Text"}
        form = TopicForm(data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_topic_form_missing_title(self):
        """Test when title is missing"""
        data = {"subtitle": "Test Topic Subtitle", "tags": "test,topic,tags", "text": "Test Topic Text"}
        form = TopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_title(self):
        """Test when title contains only whitespace"""
        data = {"title": " ", "subtitle": "Test Topic Subtitle", "tags": "test,topic,tags", "text": "Test Topic Text"}
        form = TopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_missing_text(self):
        """Test when text is missing"""
        data = {
            "title": "Test Topic Title",
            "subtitle": "Test Topic Subtitle",
            "tags": "test,topic,tags",
        }
        form = TopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_empty_text(self):
        """Test when text contains only whitespace"""
        data = {"title": "Test Topic Title", "subtitle": "Test Topic Subtitle", "tags": "test,topic,tags", "text": " "}
        form = TopicForm(data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_topic_form_text_too_long(self):
        """Test when text runs over the length limit"""
        data = {
            "title": "Test Topic Title",
            "subtitle": "Test Topic Subtitle",
            "tags": "test,topic,tags",
            "text": text_too_long,
        }
        form = TopicForm(data=data)

        self.assertFalse(form.is_valid())


class PostFormTest(TestCase):
    def test_valid_post_form(self):
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        data = {"text": "Test Post Text"}
        form = PostForm(topic, profile.user, data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_post_form_missing_text(self):
        """Test when text is missing"""
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        data = {}
        form = PostForm(topic, profile.user, data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_post_form_empty_text(self):
        """Test when text contains only whitespace"""
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        data = {"text": " "}
        form = PostForm(topic, profile.user, data=data)

        self.assertFalse(form.is_valid())

    def test_invalid_post_form_text_too_long(self):
        """Test when text runs over the length limit"""
        profile = ProfileFactory()
        _, forum = create_category_and_forum()
        topic = create_topic_in_forum(forum, profile)
        data = {
            "text": text_too_long,
        }
        form = PostForm(topic, profile.user, data=data)

        self.assertFalse(form.is_valid())
