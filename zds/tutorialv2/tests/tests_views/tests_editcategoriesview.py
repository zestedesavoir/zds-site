from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.tutorialv2.views.categories import EditCategoriesForm
from zds.utils.tests.factories import SubCategoryFactory


def publish(content):
    """Emulate the publication of a content."""
    published = publish_content(content, content.load_version())
    content.public_version = published
    content.save()


@override_for_contents()
class PermissionTests(TutorialTestMixin, TestCase):
    """Test permissions and associated behaviors, such as redirections and status codes."""

    def setUp(self):
        self.author = ProfileFactory().user
        self.category = SubCategoryFactory()
        content = PublishableContentFactory(author_list=[self.author])

        self.target_url = reverse("content:edit-categories", kwargs={"pk": content.pk})
        self.form_data = {"subcategory": self.category.pk}
        self.login_url = reverse("member-login") + "?next=" + self.target_url
        self.content_url = reverse("content:view", kwargs={"pk": content.pk, "slug": content.slug})

    def get(self):
        return self.client.get(self.target_url)

    def post(self):
        return self.client.post(self.target_url, self.form_data)

    def test_not_authenticated(self):
        """Test that unauthenticated users are redirected to the login page."""
        self.client.logout()  # ensure no user is authenticated

        with self.subTest(msg="GET"):
            response = self.get()
            self.assertRedirects(response, self.login_url)

        with self.subTest(msg="POST"):
            response = self.post()
            self.assertRedirects(response, self.login_url)

    def test_authenticated_author(self):
        """Test that authors can reach the page."""
        self.client.force_login(self.author)

        with self.subTest(msg="GET"):
            response = self.get()
            self.assertEqual(response.status_code, 200)

        with self.subTest(msg="POST"):
            response = self.post()
            self.assertRedirects(response, self.content_url)

    def test_authenticated_staff(self):
        """Test that staffs can reach the page."""
        staff = StaffProfileFactory().user
        self.client.force_login(staff)

        with self.subTest(msg="GET"):
            response = self.get()
            self.assertEqual(response.status_code, 200)

        with self.subTest(msg="POST"):
            response = self.post()
            self.assertRedirects(response, self.content_url)

    def test_authenticated_outsider(self):
        """Test that unauthorized users get a 403."""
        outsider = ProfileFactory().user
        self.client.force_login(outsider)

        with self.subTest(msg="GET"):
            response = self.get()
            self.assertEqual(response.status_code, 403)

        with self.subTest(msg="POST"):
            response = self.get()
            self.assertEqual(response.status_code, 403)


@override_for_contents()
class FunctionalTests(TutorialTestMixin, TestCase):
    """Test the behavior of the feature."""

    def setUp(self):
        self.author = StaffProfileFactory().user
        self.content = PublishableContentFactory(author_list=[self.author], add_category=False)

        self.category_0 = SubCategoryFactory()
        self.category_1 = SubCategoryFactory()

        self.url = reverse("content:edit-categories", kwargs={"pk": self.content.pk})

        self.client.force_login(self.author)

    def test_add_category(self):
        form_data = {"subcategory": [str(self.category_0.pk)]}
        self.client.post(self.url, form_data)

        categories_real = self.content.subcategory.all()
        categories_expected = [self.category_0]
        self.assertQuerysetEqual(categories_real, categories_expected)

    def test_remove_category(self):
        self.content.subcategory.add(self.category_0)
        self.assertQuerysetEqual(self.content.subcategory.all(), [self.category_0])

        form_data = {"subcategory": []}
        self.client.post(self.url, form_data)

        categories_real = self.content.subcategory.all()
        categories_expected = []
        self.assertQuerysetEqual(categories_real, categories_expected)

    def test_remove_published(self):
        self.content.subcategory.add(self.category_0)
        self.assertQuerysetEqual(self.content.subcategory.all(), [self.category_0])
        publish(self.content)

        form_data = {"subcategory": []}
        response = self.client.post(self.url, form_data, follow=True)
        self.assertContains(response, escape(EditCategoriesForm.error_messages["no_category_but_public"]))
        self.assertQuerysetEqual(self.content.subcategory.all(), [self.category_0])
