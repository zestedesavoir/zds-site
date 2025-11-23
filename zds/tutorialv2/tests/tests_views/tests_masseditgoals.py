from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.goals import Goal
from zds.tutorialv2.tests.factories import GoalFactory, PublishableContentFactory, PublishedContentFactory
from zds.tutorialv2.views.goals import MassEditGoalsForm


class MassEditGoalsPermissionTests(TestCase):
    def setUp(self):
        self.user = ProfileFactory().user
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.content1 = PublishableContentFactory()
        self.content1.authors.add(self.author)

        self.content2 = PublishableContentFactory()
        self.content2.authors.add(self.author)

        self.url = reverse("content:mass-edit-goals")
        self.login_url = reverse("member-login") + f"?next={self.url}"

    def test_unauthenticated_forbidden(self):
        """
        Unauthenticated users shall be redirected to the login page.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, self.login_url)

    def test_user_forbidden(self):
        """Mere users shall not have access to the view."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_staff_authorized(self):
        """Staff members shall have access to the view."""
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class MassEditGoalsFormTests(TestCase):
    def setUp(self):
        self.content_id = PublishableContentFactory().id
        self.goal_id = GoalFactory().id

    def test_invalid_content_id(self):
        data = {
            "goal_id": self.goal_id,
            "content_id": "invalid_content_id",  # not even an integer
        }
        self.assertFalse(MassEditGoalsForm(data).is_valid())

    def test_nonexistent_content_id(self):
        data = {
            "goal_id": self.goal_id,
            "content_id": 42,  # a plausible pk, but non existent
        }
        self.assertFalse(MassEditGoalsForm(data).is_valid())

    def test_invalid_goal_id(self):
        data = {
            "goal_id": "some_invalid_data",  # not even an integer
            "content_id": self.content_id,
        }
        self.assertFalse(MassEditGoalsForm(data).is_valid())

    def test_nonexistent_goal_id(self):
        data = {
            "goal_id": 42,  # a plausible pk, but non existent
            "content_id": self.content_id,
        }
        self.assertFalse(MassEditGoalsForm(data).is_valid())

    def test_nominal(self):
        data = {
            "goal_id": self.goal_id,
            "content_id": self.content_id,
            # no need to add "activated" field, it is optional
        }
        self.assertTrue(MassEditGoalsForm(data).is_valid())


class MassEditGoalsFunctionalTests(TestCase):
    def setUp(self):
        self.content = PublishableContentFactory()
        self.goal = GoalFactory()
        self.staff = StaffProfileFactory()
        self.client.force_login(self.staff.user)

    def test_nominal_add(self):
        """When requesting an addition, the view shall add the goal to the content's goals."""
        # Note: the "activated" parameter is the current state, not the desired state.
        form_args = {"activated": True, "goal_id": self.goal.pk, "content_id": self.content.pk}
        response = self.client.post(reverse("content:mass-edit-goals"), form_args)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.content.goals.all()), [self.goal])

    def test_nominal_remove(self):
        """When requesting a removal, the view shall remove the goal from the content's goals."""

        # Setup for this test
        self.content.goals.add(self.goal)
        self.assertEqual(list(self.content.goals.all()), [self.goal])

        form_args = {"activated": False, "goal_id": self.goal.pk, "content_id": self.content.pk}
        response = self.client.post(reverse("content:mass-edit-goals"), form_args)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.content.goals.all()), [])

    def test_error(self):
        """When sending an invalid request, the view answers with a code 400, but no error is displayed."""
        response = self.client.post(reverse("content:mass-edit-goals"), {})
        self.assertEqual(response.status_code, 400)


class TestMassEditGoalsFilterTests(TestCase):
    def setUp(self):
        self.contents = [
            PublishedContentFactory(),
            PublishedContentFactory(),
            PublishedContentFactory(),
            PublishedContentFactory(),
        ]
        self.goals = [GoalFactory(), GoalFactory()]

        self.contents[1].goals.add(self.goals[0])
        self.contents[2].goals.add(self.goals[1])
        self.contents[3].goals.add(self.goals[0])
        self.contents[3].goals.add(self.goals[1])

        self.staff = StaffProfileFactory()

        self.url = reverse("content:mass-edit-goals")

        self.client.force_login(self.staff.user)

    def test_filter_counts(self):
        """The counts displayed next to the filter links shall be correct."""
        response = self.client.get(self.url)
        self.assertEqual(response.context["num_all"], len(self.contents))
        self.assertEqual(response.context["num_not_classified"], 1)

    def test_filter_all(self):
        """When no filter are used, the view shall display all contents."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for content in self.contents:
            self.assertContains(response, content.title)

    def test_filter_goal(self):
        """The filter for a given goal shall display only contents with this goal."""
        response = self.client.get(self.url + f"?{self.goals[0].slug}")
        self.assertNotContains(response, self.contents[0].title)
        self.assertContains(response, self.contents[1].title)
        self.assertNotContains(response, self.contents[2].title)
        self.assertContains(response, self.contents[3].title)

    def test_filter_no_goals(self):
        """The filter for no goals shall display only contents with no goals."""
        response = self.client.get(self.url + "?" + Goal.SLUG_UNCLASSIFIED)
        self.assertContains(response, self.contents[0].title)
        self.assertNotContains(response, self.contents[1].title)
        self.assertNotContains(response, self.contents[2].title)
        self.assertNotContains(response, self.contents[3].title)
