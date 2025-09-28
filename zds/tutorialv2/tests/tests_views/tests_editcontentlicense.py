from django.test import TestCase
from django.urls import reverse

from zds.member.models import Profile
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.licence import EditContentLicense, EditContentLicenseForm
from zds.utils.tests.factories import LicenceFactory


@override_for_contents()
class EditContentLicensePermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a license
        self.licence = LicenceFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-license", kwargs={"pk": self.content.pk})
        self.form_data = {"license": self.licence.pk, "update_preferred_license": False}
        self.content_data = {"pk": self.content.pk, "slug": self.content.slug}
        self.content_url = reverse("content:view", kwargs=self.content_data)
        self.login_url = reverse("member-login") + "?next=" + self.form_url

    def test_not_authenticated(self):
        """Test that on form submission, unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that on form submission, authors are redirected to the content page."""
        self.client.force_login(self.author)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff(self):
        """Test that on form submission, staffs are redirected to the content page."""
        self.client.force_login(self.staff)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_outsider(self):
        """Test that on form submission, unauthorized users get a 403."""
        self.client.force_login(self.outsider)
        response = self.client.post(self.form_url, self.form_data)
        self.assertEqual(response.status_code, 403)


@override_for_contents()
class EditContentLicenseWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create a license
        self.license = LicenceFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user], add_license=False)

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-license", kwargs={"pk": self.content.pk})
        self.error_messages = EditContentLicenseForm.declared_fields["license"].error_messages
        self.success_message_license = EditContentLicense.success_message_license
        self.success_message_profile_update = EditContentLicense.success_message_profile_update

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        self.client.force_login(self.author.user)

    def get_test_cases(self):
        return {
            "empty_form": {"inputs": {}, "expected_outputs": [self.error_messages["required"]]},
            "empty_fields": {
                "inputs": {"license": "", "update_preferred_license": ""},
                "expected_outputs": [self.error_messages["required"]],
            },
            "invalid_license": {
                "inputs": {"license": "valeur_bidonnée", "update_preferred_license": ""},
                "expected_outputs": [self.error_messages["invalid_choice"]],
            },
            "success_license": {
                "inputs": {"license": self.license.pk, "update_preferred_license": False},
                "expected_outputs": [self.success_message_license],
            },
            "success_license_profile": {
                "inputs": {"license": self.license.pk, "update_preferred_license": True},
                "expected_outputs": [self.success_message_license, self.success_message_profile_update],
            },
        }

    def test_form_workflow(self):
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                response = self.client.post(self.form_url, case["inputs"], follow=True)
                for msg in case["expected_outputs"]:
                    self.assertContains(response, msg)


@override_for_contents()
class EditContentLicenseFunctionalTests(TutorialTestMixin, TestCase):
    """Test the detailed behavior of the feature, such as updates of the database or repositories."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create licenses
        self.license_1 = LicenceFactory()
        self.license_2 = LicenceFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user], add_license=False)

        # Get information to be reused in tests
        self.form_url = reverse("content:edit-license", kwargs={"pk": self.content.pk})

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        self.client.force_login(self.author.user)

    def test_form_function(self):
        """Test many use cases for the form."""
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                self.enforce_preconditions(case["preconditions"])
                self.post_form(case["inputs"])
                self.check_effects(case["expected_outputs"])

    def get_test_cases(self):
        """List test cases for the license editing form."""
        return {
            "from blank to license 1, no preference, no udpate of preferences": {
                "preconditions": {"content_license": None, "preferred_license": None},
                "inputs": {"license": self.license_1, "update_preferred_license": False},
                "expected_outputs": {"content_license": self.license_1, "preferred_license": None},
            },
            "from blank to license 1, no preference, udpate of preferences": {
                "preconditions": {"content_license": None, "preferred_license": None},
                "inputs": {"license": self.license_1, "update_preferred_license": True},
                "expected_outputs": {"content_license": self.license_1, "preferred_license": self.license_1},
            },
            "from blank to license 2, no preference, no udpate of preferences": {
                "preconditions": {"content_license": None, "preferred_license": None},
                "inputs": {"license": self.license_2, "update_preferred_license": False},
                "expected_outputs": {"content_license": self.license_2, "preferred_license": None},
            },
            "from blank to license 2, no preference, udpate of preferences": {
                "preconditions": {"content_license": None, "preferred_license": None},
                "inputs": {"license": self.license_2, "update_preferred_license": True},
                "expected_outputs": {"content_license": self.license_2, "preferred_license": self.license_2},
            },
            "from blank to license 1, preference, no udpate of preferences": {
                "preconditions": {"content_license": None, "preferred_license": self.license_2},
                "inputs": {"license": self.license_1, "update_preferred_license": False},
                "expected_outputs": {"content_license": self.license_1, "preferred_license": self.license_2},
            },
            "from blank to license 1, preference, udpate of preferences": {
                "preconditions": {"content_license": None, "preferred_license": self.license_2},
                "inputs": {"license": self.license_1, "update_preferred_license": True},
                "expected_outputs": {"content_license": self.license_1, "preferred_license": self.license_1},
            },
            "from license 1 to license 2, no preference, no udpate of preferences": {
                "preconditions": {"content_license": self.license_1, "preferred_license": None},
                "inputs": {"license": self.license_2, "update_preferred_license": False},
                "expected_outputs": {"content_license": self.license_2, "preferred_license": None},
            },
            "from license 1 to license 2, no preference, udpate of preferences": {
                "preconditions": {"content_license": self.license_1, "preferred_license": None},
                "inputs": {"license": self.license_2, "update_preferred_license": True},
                "expected_outputs": {"content_license": self.license_2, "preferred_license": self.license_2},
            },
        }

    def enforce_preconditions(self, preconditions):
        """Prepare the test environment to match given preconditions"""

        # Enforce preconditions for license in database
        self.content.licence = preconditions["content_license"]
        self.content.save()
        self.assertEqual(self.content.licence, preconditions["content_license"])

        # Enforce preconditions for license in repository
        versioned = self.content.load_version()
        versioned.licence = preconditions["content_license"]
        sha = versioned.repo_update_top_container("Title", self.content.slug, "introduction", "conclusion")
        updated_versioned = self.content.load_version(sha)
        self.assertEqual(updated_versioned.licence, preconditions["content_license"])

        # Enforce preconditions for preferred license
        self.author.licence = preconditions["preferred_license"]
        self.author.save()
        updated_profile = Profile.objects.get(pk=self.author.pk)
        self.assertEqual(updated_profile.licence, preconditions["preferred_license"])

    def post_form(self, inputs):
        """Post the form with given inputs."""
        form_data = {"license": inputs["license"].pk, "update_preferred_license": inputs["update_preferred_license"]}
        self.client.post(self.form_url, form_data)

    def check_effects(self, expected_outputs):
        """Check the effects of having sent the form."""

        # Check updating of the database
        updated_content = PublishableContent.objects.get(pk=self.content.pk)
        updated_profile = Profile.objects.get(pk=self.author.pk)
        self.assertEqual(updated_content.licence, expected_outputs["content_license"])
        self.assertEqual(updated_profile.licence, expected_outputs["preferred_license"])

        # Check updating of the repository
        versioned = updated_content.load_version()
        self.assertEqual(versioned.licence, expected_outputs["content_license"])
