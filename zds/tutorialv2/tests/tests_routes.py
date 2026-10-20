from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.models.database import PublishableContent, PublishedContent
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import ContainerFactory, PublishableContentFactory


def mock_publication_process(content: PublishableContent):
    published = publish_content(content, content.load_version())
    content.sha_public = content.sha_draft
    content.public_version = published
    content.save()


class BasicRouteTestsMixin(TutorialTestMixin):
    def setUp(self):
        self.build_content(self.content_type)
        mock_publication_process(self.content)

    def build_content(self, type):
        self.content = PublishableContentFactory()
        self.content.type = type
        self.content.save()
        content_versioned = self.content.load_version()
        self.container = ContainerFactory(parent=content_versioned, db_object=self.content)
        self.subcontainer = ContainerFactory(parent=self.container, db_object=self.content)

    def test_view(self):
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
        }
        self.assert_can_be_reached(self.view_name, route_args)

    def test_view_container_one_level_deep(self):
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
            "container_slug": self.container.slug,
        }
        self.assert_can_be_reached(self.container_view_name, route_args)

    def test_view_container_two_level_deep(self):
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
            "parent_container_slug": self.container.slug,
            "container_slug": self.subcontainer.slug,
        }
        self.assert_can_be_reached(self.container_view_name, route_args)

    def test_published_content_absolute_url(self):
        # Given
        published = self.content.public_version

        # When
        url = published.get_absolute_url()

        # Then
        expected_url = reverse(self.view_name, kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.assertEqual(url, expected_url)

    def test_admin_view_on_site(self):
        # Given
        admin = ProfileFactory().user
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.client.force_login(admin)
        published = self.content.public_version

        # When
        content_type = ContentType.objects.get_for_model(PublishedContent)
        url = reverse("admin:view_on_site", args=[content_type.pk, published.pk])
        response = self.client.get(url)

        # Then
        expected_url = reverse(self.view_name, kwargs={"pk": self.content.pk, "slug": self.content.slug})
        self.assertRedirects(response, response.wsgi_request.build_absolute_uri(expected_url))

    def assert_can_be_reached(self, route, route_args):
        url = reverse(route, kwargs=route_args)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


@override_for_contents()
class OpinionDisplayRoutesTests(BasicRouteTestsMixin, TestCase):
    content_type = "OPINION"
    view_name = "opinion:view"
    container_view_name = "opinion:view-container"


@override_for_contents()
class ArticlesDisplayRoutesTests(BasicRouteTestsMixin, TestCase):
    content_type = "ARTICLE"
    view_name = "article:view"
    container_view_name = "article:view-container"


@override_for_contents()
class TutorialsDisplayRoutesTests(BasicRouteTestsMixin, TestCase):
    content_type = "TUTORIAL"
    view_name = "tutorial:view"
    container_view_name = "tutorial:view-container"
