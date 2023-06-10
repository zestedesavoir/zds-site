from django.test import TestCase
from django.urls import reverse

from zds.tutorialv2.tests.factories import GoalFactory, PublishedContentFactory


class ViewContentsByGoalTests(TestCase):
    def setUp(self):
        self.goals = [GoalFactory(), GoalFactory()]
        self.contents = [PublishedContentFactory(), PublishedContentFactory()]

    def test_page_content(self):
        """Test roughly that what is expected is in the page."""
        response = self.client.get(reverse("content:view-goals"))
        self.assertEqual(response.status_code, 200)
        for goal in self.goals:
            self.assertContains(response, goal.name)
        for content in self.contents:
            self.assertContains(response, content.title)

    def test_forbid_slug_unclassified(self):
        goal = Goal(name="Invalid", slug=Goal.SLUG_UNCLASSIFIED)
        self.assertRaises(ValidationError, goal.full_clean)

        goal = Goal(name="Almost invalid", slug=Goal.SLUG_UNCLASSIFIED + "z")
        goal.full_clean()

        goal = Goal(name="Valid", slug="valid-slug")
        goal.full_clean()
