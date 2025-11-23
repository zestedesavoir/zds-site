from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from zds.tutorialv2.models.goals import Goal
from zds.tutorialv2.tests.factories import GoalFactory, PublishedContentFactory


class ViewContentsByGoalTests(TestCase):
    def setUp(self):
        self.goals = [GoalFactory(), GoalFactory()]
        self.contents = [PublishedContentFactory(), PublishedContentFactory()]

        self.contents[0].goals.add(self.goals[0])
        self.contents[0].save()

    def test_display_all_contents(self):
        # By default, the URL without parameters display all contents:
        response = self.client.get(reverse("content:view-goals"))
        self.assertEqual(response.status_code, 200)
        for goal in self.goals:
            self.assertContains(response, goal.name)
        for content in self.contents:
            self.assertContains(response, content.title)

    def test_display_contents_with_goal(self):
        # Display only contents having the goal self.goals[0]:
        response = self.client.get(reverse("content:view-goals") + "?" + self.goals[0].slug)
        self.assertEqual(response.status_code, 200)
        for goal in self.goals:
            self.assertContains(response, goal.name)
        self.assertContains(response, self.contents[0].title)
        self.assertNotContains(response, self.contents[1].title)

    def test_display_contents_without_goal(self):
        response = self.client.get(reverse("content:view-goals") + "?" + Goal.SLUG_UNCLASSIFIED)
        self.assertEqual(response.status_code, 200)
        for goal in self.goals:
            self.assertContains(response, goal.name)
        self.assertNotContains(response, self.contents[0].title)
        self.assertContains(response, self.contents[1].title)

    def test_forbid_slug_unclassified(self):
        goal = Goal(name="Invalid", slug=Goal.SLUG_UNCLASSIFIED)
        self.assertRaises(ValidationError, goal.full_clean)

        goal = Goal(name="Almost invalid", slug=Goal.SLUG_UNCLASSIFIED + "z")
        goal.full_clean()

        goal = Goal(name="Valid", slug="valid-slug")
        goal.full_clean()
