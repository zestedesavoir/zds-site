from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from zds.gallery.tests.factories import UserGalleryFactory
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.models.database import PublishedContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import (
    ContentContributionRoleFactory,
    PublishableContentFactory,
    PublishedContentFactory,
)
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


@override_for_contents()
class EventListPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.events_list_url = reverse("content:events", kwargs={"pk": self.content.pk})
        self.login_url = reverse("member-login") + "?next=" + self.events_list_url

    def test_not_authenticated(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated
        response = self.client.get(self.events_list_url)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that authors have access to the page."""
        self.client.force_login(self.author)
        response = self.client.get(self.events_list_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_staff(self):
        """Test that staffs have access to the page."""
        self.client.force_login(self.staff)
        response = self.client.get(self.events_list_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_outsider(self):
        """Test that unauthorized users get a 403."""
        self.client.force_login(self.outsider)
        response = self.client.get(self.events_list_url)
        self.assertEqual(response.status_code, 403)


@override_for_contents()
class EventListTests(TutorialTestMixin, TestCase):
    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.coauthor = ProfileFactory().user
        self.contributor = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.anonymous = UserFactory(username=settings.ZDS_APP["member"]["anonymous_account"], password="anything")
        self.external = UserFactory(username=settings.ZDS_APP["member"]["external_account"], password="anything")
        self.bot = UserFactory(username=settings.ZDS_APP["member"]["bot_account"], password="anything")
        self.role = ContentContributionRoleFactory()

    def test_events_involving_unregistered_users(self):
        """Test accessing the event list with actions involving unregistered users."""
        article = PublishedContentFactory(type="ARTICLE", author_list=[self.author])

        self.client.force_login(self.author)

        # Add a coauthor
        result = self.client.post(
            reverse("content:add-author", args=[article.pk]), {"username": self.coauthor.username}, follow=False
        )
        self.assertEqual(result.status_code, 302)

        # Add a contributor
        form_data = {
            "username": self.contributor,
            "contribution_role": self.role.pk,
            "comment": "Foo",
        }
        result = self.client.post(reverse("content:add-contributor", args=[article.pk]), form_data, follow=True)
        self.assertEqual(result.status_code, 200)

        # Unregister users
        for user in [self.author, self.coauthor, self.contributor]:
            self.client.force_login(user)
            response = self.client.post(reverse("member-unregister"), {"password": "hostel77"}, follow=False)
            self.assertEqual(response.status_code, 302)

        # Access the event list page
        self.client.force_login(self.staff)
        response = self.client.get(reverse("content:events", args=[article.pk]))
        self.assertEqual(response.status_code, 200)
