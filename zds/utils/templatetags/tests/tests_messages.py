from django.contrib.messages.storage.base import Message
from django.contrib.messages import constants, utils

from django.test import SimpleTestCase

from zds.utils.templatetags.messages import messages


LEVEL_TAGS = utils.get_level_tags()


class FunctionTests(SimpleTestCase):

    def test_standard_message(self):
        test_messages = [Message(constants.DEBUG, 'some debug message')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some debug message', 'tags': LEVEL_TAGS[constants.DEBUG]}]})
        test_messages = [Message(constants.INFO, 'some info message')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some info message', 'tags': LEVEL_TAGS[constants.INFO]}]})
        test_messages = [Message(constants.SUCCESS, 'some success message')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some success message', 'tags': LEVEL_TAGS[constants.SUCCESS]}]})
        test_messages = [Message(constants.WARNING, 'some warning message')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some warning message', 'tags': LEVEL_TAGS[constants.WARNING]}]})
        test_messages = [Message(constants.ERROR, 'some error message')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some error message', 'tags': LEVEL_TAGS[constants.ERROR]}]})

    def test_no_messages(self):
        self.assertEqual(messages([]), {'messages': []})

    def test_multiple_messages(self):
        test_messages = [Message(constants.DEBUG, 'some debug message'), Message(constants.INFO, 'some info message')]
        expected = {'messages': [
            {'text': 'some debug message', 'tags': LEVEL_TAGS[constants.DEBUG]},
            {'text': 'some info message', 'tags': LEVEL_TAGS[constants.INFO]}
        ]}
        self.assertEqual(messages(test_messages), expected)

    def test_dirty_message(self):
        test_messages = [Message(constants.DEBUG, '[\'some debug message\']')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some debug message', 'tags': LEVEL_TAGS[constants.DEBUG]}]})
        test_messages = [Message(constants.INFO, '[\'some info message\']')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some info message', 'tags': LEVEL_TAGS[constants.INFO]}]})
        test_messages = [Message(constants.SUCCESS, '[\'some success message\']')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some success message', 'tags': LEVEL_TAGS[constants.SUCCESS]}]})
        test_messages = [Message(constants.WARNING, '[\'some warning message\']')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some warning message', 'tags': LEVEL_TAGS[constants.WARNING]}]})
        test_messages = [Message(constants.ERROR, '[\'some error message\']')]
        self.assertEqual(messages(test_messages), {'messages': [{'text': 'some error message', 'tags': LEVEL_TAGS[constants.ERROR]}]})

    def test_multiple_dirty_message(self):
        test_messages = [Message(constants.DEBUG, '[\'some debug message\']'), Message(constants.INFO, '[\'some info message\']')]
        expected = {'messages': [
            {'text': 'some debug message', 'tags': LEVEL_TAGS[constants.DEBUG]},
            {'text': 'some info message', 'tags': LEVEL_TAGS[constants.INFO]}
        ]}
        self.assertEqual(messages(test_messages), expected)
