from django.contrib.messages import constants, utils
from django.contrib.messages.storage.base import Message
from django.test import SimpleTestCase

from zds.utils.templatetags.messages import messages

LEVEL_TAGS = utils.get_level_tags()


class FunctionTests(SimpleTestCase):
    tags = [constants.DEBUG, constants.INFO, constants.SUCCESS, constants.WARNING, constants.ERROR]

    def test_messages(self):
        for tag in self.tags:
            txt = f"some message with {repr(tag)}"

            test_messages = [Message(tag, txt)]
            self.assertEqual(
                messages(test_messages), {"messages": [{"text": txt, "tags": LEVEL_TAGS[tag]}]}
            )  # clean one

            txt = f"['some dirty message with {repr(tag)}']"
            txt_altered = txt.replace("['", "").replace("']", "")
            test_messages = [Message(tag, txt)]
            self.assertEqual(
                messages(test_messages), {"messages": [{"text": txt_altered, "tags": LEVEL_TAGS[tag]}]}
            )  # dirty one

    def test_no_messages(self):
        self.assertEqual(messages([]), {"messages": []})

    def test_multiple_messages(self):
        test_messages = [Message(constants.DEBUG, "some debug message"), Message(constants.INFO, "some info message")]

        expected = {
            "messages": [
                {"text": "some debug message", "tags": LEVEL_TAGS[constants.DEBUG]},
                {"text": "some info message", "tags": LEVEL_TAGS[constants.INFO]},
            ]
        }
        self.assertEqual(messages(test_messages), expected)

        test_messages = [
            Message(constants.DEBUG, "['some debug message']"),
            Message(constants.INFO, "['some info message']"),
        ]

        expected = {
            "messages": [
                {"text": "some debug message", "tags": LEVEL_TAGS[constants.DEBUG]},
                {"text": "some info message", "tags": LEVEL_TAGS[constants.INFO]},
            ]
        }

        self.assertEqual(messages(test_messages), expected)
