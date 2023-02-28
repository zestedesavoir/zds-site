from django.test import TestCase

from zds.tutorialv2.models.database import ContentSuggestion, PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory


@override_for_contents()
class ContentSuggestionTests(TutorialTestMixin, TestCase):
    def setUp(self):
        self.publication = PublishableContentFactory()
        self.suggested_publications = [
            PublishableContentFactory(),
            PublishableContentFactory(),
            PublishableContentFactory(),
            PublishableContentFactory(),
        ]

        # Make some suggested publications public, but not all.
        for publication in self.suggested_publications[:-1]:
            self.mock_publication_process(publication)

        ContentSuggestion(publication=self.publication, suggestion=self.suggested_publications[0]).save()
        ContentSuggestion(publication=self.publication, suggestion=self.suggested_publications[1]).save()
        ContentSuggestion(publication=self.publication, suggestion=self.suggested_publications[2]).save()

    def test_random_public_suggestions(self):
        all_suggestions = ContentSuggestion.objects.filter(publication=self.publication)
        all_suggestions_count = all_suggestions.count()
        public_suggestions = [suggestion for suggestion in all_suggestions if suggestion.suggestion.in_public()]
        public_suggestions_count = len(public_suggestions)
        for count in range(all_suggestions_count):
            suggestions = ContentSuggestion.get_random_public_suggestions(self.publication, count)
            self.assertEqual(len(suggestions), min(count, public_suggestions_count))
            for suggestion in suggestions:
                self.assertTrue(suggestion.suggestion.in_public())

    def mock_publication_process(self, publication: PublishableContent) -> ():
        """
        Make the publication behave, for the purpose of the test, as if it had been published.
        This is not extremely robust, but better than not testing.
        """
        publication.sha_public = "123456"
        publication.save()
        self.assertTrue(publication.in_public())
