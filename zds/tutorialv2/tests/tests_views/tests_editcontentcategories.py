from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.views.editorialization import EditContentCategories
from zds.tutorialv2.forms import EditContentCategoriesForm
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, SubCategoryFactory


@override_for_contents()
class EditContentCategoriesPermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        # Create users
        self.author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.outsider = ProfileFactory().user

        # Create a category
        self.category = SubCategoryFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author])

        # Get information to be reused in tests
        self.form_url = reverse('content:edit-categories', kwargs={'pk': self.content.pk})
        self.form_data = {'categories': [self.category]}
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
class EditContentCategoriesWorkflowTests(TutorialTestMixin, TestCase):
    """Test the workflow of the form, such as validity errors and success messages."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create a category
        self.category = SubCategoryFactory()

        # Create a draft content
        self.content = PublishableContentFactory(author_list=[self.author.user], add_license=False)

        # Create a published content
        self.published_content = PublishableContentFactory(author_list=[self.author.user], add_license=False)
        publish_content(self.published_content,
                        self.published_content.load_version_or_404(self.published_content.sha_draft))
        self.published_content.save()  # update object info to take the publication into account

        # Get information to be reused in tests
        self.error_messages = EditContentCategoriesForm.declared_fields['subcategory'].error_messages
        self.success_message = EditContentCategories.success_message

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        login_success = self.client.login(username=self.author.user.username, password='hostel77')
        self.assertTrue(login_success)

    def form_url(self, is_published):
        if is_published:
            content = self.published_content
        else:
            content = self.content
        return reverse('content:edit-categories', kwargs={'pk': content.pk})

    def get_test_cases(self):
        return {
            'empty_form': {
                'config': {'is_published': False},
                'inputs': {},
                'expected_outputs': [self.success_message]
            },
            'success_category_one': {
                'config': {'is_published': False},
                'inputs': {'subcategory': self.category.pk},
                'expected_outputs': [self.success_message]
            },
            'invalid_category': {
                'config': {'is_published': False},
                'inputs': {'subcategory': '42'},  # valid form for a pk, but the value does not exist
                'expected_outputs': [self.error_messages['invalid_choice']]
            },
            'invalid_category_pk': {
                'config': {'is_published': False},
                'inputs': {'subcategory': 'valeur bidonnée'},  # value that fails to convert to a valid pk
                'expected_outputs': [self.error_messages['invalid_pk_value'] % {'pk': 'valeur bidonnée'}]
            },
            'empty_when_published': {
                'config': {'is_published': True},
                'inputs': {},
                'expected_outputs': [self.error_messages['empty_when_published']]
            },
            'success_category_when_published': {
                'config': {'is_published': True},
                'inputs': {'subcategory': self.category.pk},
                'expected_outputs': [self.success_message]
            },
        }

    def test_form_workflow(self):
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                form_url = self.form_url(case['config']['is_published'])
                response = self.client.post(form_url, case['inputs'], follow=True)
                for msg in case['expected_outputs']:
                    self.assertContains(response, escape(msg))  # the response is escaped, so we escape the message too


@override_for_contents()
class EditContentCategoriesFunctionalTests(TutorialTestMixin, TestCase):
    """Test the detailed behavior of the feature, such as updates of the database."""

    def setUp(self):
        # Create a user
        self.author = ProfileFactory()

        # Create some categories
        self.category1 = SubCategoryFactory()
        self.category2 = SubCategoryFactory()

        # Create a content
        self.content = PublishableContentFactory(author_list=[self.author.user], add_license=False)

        # Get information to be reused in tests
        self.form_url = reverse('content:edit-categories', kwargs={'pk': self.content.pk})

        # Log in with an authorized user (e.g the author of the content) to perform the tests
        login_success = self.client.login(username=self.author.user.username, password='hostel77')
        self.assertTrue(login_success)

    def test_form_function(self):
        """Test many use cases for the form."""
        test_cases = self.get_test_cases()
        for case_name, case in test_cases.items():
            with self.subTest(msg=case_name):
                # Prepare the test environment to match given preconditions
                self.content.subcategory.set(case['preconditions']['subcategory'])
                self.assertEqual(list(self.content.subcategory.all()), case['preconditions']['subcategory'])

                # Post the form with given inputs
                form_data = {'subcategory': [sc.pk for sc in case['inputs']['subcategory']]}
                self.client.post(self.form_url, form_data)

                # Check the effects of having sent the form
                updated_content = PublishableContent.objects.get(pk=self.content.pk)
                self.assertEqual(list(updated_content.subcategory.all()), case['expected_outputs']['subcategory'])

    def get_test_cases(self):
        """List test cases for the categories editing form."""
        return {
            'from blank to one category': {
                'preconditions': {'subcategory': []},
                'inputs': {'subcategory': [self.category1]},
                'expected_outputs': {'subcategory': [self.category1]}
            },
            'from blank to two categories': {
                'preconditions': {'subcategory': []},
                'inputs': {'subcategory': [self.category1, self.category2]},
                'expected_outputs': {'subcategory': [self.category1, self.category2]}
            },
            'remove all categories (1)': {
                'preconditions': {'subcategory': [self.category1]},
                'inputs': {'subcategory': []},
                'expected_outputs': {'subcategory': []}
            },
            'remove all categories (2)': {
                'preconditions': {'subcategory': [self.category1, self.category2]},
                'inputs': {'subcategory': []},
                'expected_outputs': {'subcategory': []}
            },
            'add one category': {
                'preconditions': {'subcategory': [self.category1]},
                'inputs': {'subcategory': [self.category1, self.category2]},
                'expected_outputs': {'subcategory': [self.category1, self.category2]}
            },
            'remove one category': {
                'preconditions': {'subcategory': [self.category1, self.category2]},
                'inputs': {'subcategory': [self.category2]},
                'expected_outputs': {'subcategory': [self.category2]}
            },
        }
