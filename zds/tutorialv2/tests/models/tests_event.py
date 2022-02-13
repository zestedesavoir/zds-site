from django.test import TestCase

from zds.member.factories import ProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory
from zds.tutorialv2.models.events import Event, types


class TestEvent(TestCase):
    def test_event_descriptions(self):
        content = PublishableContentFactory()
        author = ProfileFactory().user
        for _, type in types.items():
            event = Event(
                content=content,
                type=type,
                action="test",
                performer=author,
                author=author,
                contributor=author,
            )
            event.save()
            print(event.description)
            self.assertNotEqual(event.description, "")
