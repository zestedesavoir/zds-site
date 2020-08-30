from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.views.contents import EditContentTitle
from zds.tutorialv2.forms import EditContentTitleForm
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory


@override_for_contents()
class EditContentTitlePermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.form_url = reverse('content:edit-title', kwargs={'pk': self.content.pk})
        self.form_data = {'title': 'This very title is bidonné but valid'}
        self.content_data = {'pk': self.content.pk, 'slug': self.content.slug}
        self.content_url = reverse('content:view', kwargs=self.content_data)
        self.login_url = reverse('member-login') + '?next=' + self.form_url

    def test_not_authenticated(self):
        """Test that on form submission, unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that on form submission, authors are redirected to the content page."""
        login_success = self.client.login(username=self.author.username, password='hostel77')
        self.assertTrue(login_success)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_staff(self):
        """Test that on form submission, staffs are redirected to the content page."""
        login_success = self.client.login(username=self.staff.username, password='hostel77')
        self.assertTrue(login_success)
        response = self.client.post(self.form_url, self.form_data)
        self.assertRedirects(response, self.content_url)

    def test_authenticated_outsider(self):
        """Test that on form submission, unauthorized users get a 403."""
        login_success = self.client.login(username=self.outsider.username, password='hostel77')
        self.assertTrue(login_success)
        response = self.client.post(self.form_url, self.form_data)
        self.assertEquals(response.status_code, 403)


@override_for_contents()
class EditContentTitleWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user])

        # Get information to be reused in tests
        self.form_url = reverse('content:edit-title', kwargs={'pk': self.content.pk})
        self.error_messages = EditContentTitleForm.declared_fields['title'].error_messages
        self.success_message = EditContentTitle.success_message

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        login_success = self.client.login(username=self.author.user.username, password='hostel77')
        self.assertTrue(login_success)

    def get_test_cases(self):
        title_with_invalid_slug = '?'
        title_too_long = 't' * (PublishableContent._meta.get_field('title').max_length + 1)
        return {
            'empty_form': {
                'inputs': {},
                'expected_outputs': [self.error_messages['required']]
            },
            'empty_fields': {
                'inputs': {'title': ''},
                'expected_outputs': [self.error_messages['required']]
            },
            'invalid_title_slug': {
                'inputs': {'title': title_with_invalid_slug},
                'expected_outputs': [self.error_messages['invalid_slug']]
            },
            'too_long': {
                'inputs': {'title': title_too_long},
                'expected_outputs': [self.error_messages['max_length']]
            },
            'success': {
                'inputs': {'title': 'Titre bien bidonné mais valide'},
                'expected_outputs': [self.success_message]
            },
        }

    def test_form_workflow(self):
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                response = self.client.post(self.form_url, case['inputs'], follow=True)
                for msg in case['expected_outputs']:
                    self.assertContains(response, escape(msg))


@override_for_contents()
class EditContentTitleFunctionalTests(TutorialTestMixin, TestCase):
    """Test the detailed behavior of the feature, such as updates of the database or repositories."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user])
        self.initial_title = self.content.title
        self.new_title = 'The other title, definitely different from the other'

        # Get information to be reused in tests
        self.form_url = reverse('content:edit-title', kwargs={'pk': self.content.pk})

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        login_success = self.client.login(username=self.author.user.username, password='hostel77')
        self.assertTrue(login_success)

    def test_basic_functionality(self):
        """Test main use case for the form."""

        # Send the form
        form_data = {'title': self.new_title}
        self.client.post(self.form_url, form_data)

        # Check updating of the database
        updated_content = PublishableContent.objects.get(pk=self.content.pk)
        self.assertEqual(updated_content.title, self.new_title)

        # Check updating of the repository
        versioned = updated_content.load_version()
        self.assertEqual(versioned.title, self.new_title)
