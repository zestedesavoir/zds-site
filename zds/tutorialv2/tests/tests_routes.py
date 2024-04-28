from django.test import TestCase
from django.urls import reverse

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.tests import override_for_contents, TutorialTestMixin
from zds.tutorialv2.tests.factories import PublishableContentFactory, ContainerFactory


@override_for_contents()
class BasicRouteTests(TestCase, TutorialTestMixin):
    def setUp(self):
        self.build_content(self.content_type)
        self.mock_publication_process(self.content)

    def build_content(self, type):
        self.content = PublishableContentFactory()
        self.content.type = type
        self.content.save()
        content_versioned = self.content.load_version()
        self.container = ContainerFactory(parent=content_versioned, db_object=self.content)
        self.subcontainer = ContainerFactory(parent=self.container, db_object=self.content)

    def assert_can_be_reached(self, route, route_args):
        url = reverse(route, kwargs=route_args)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def mock_publication_process(self, content: PublishableContent):
        published = publish_content(content, content.load_version())
        content.sha_public = content.sha_draft
        content.public_version = published
        content.save()


class OpinionDisplayRoutesTests(BasicRouteTests):
    content_type = "OPINION"

    def test_view(self):
        route = "opinion:view"
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
        }
        self.assert_can_be_reached(route, route_args)

    def test_view_container_one_level_deep(self):
        route = "opinion:view-container"
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
            "container_slug": self.container.slug,
        }
        self.assert_can_be_reached(route, route_args)

    def test_view_container_two_level_deep(self):
        route = "opinion:view-container"
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
            "parent_container_slug": self.container.slug,
            "container_slug": self.subcontainer.slug,
        }
        self.assert_can_be_reached(route, route_args)


class ArticlesDisplayRoutesTests(BasicRouteTests):
    content_type = "ARTICLE"

    def test_view(self):
        route = "article:view"
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
        }
        self.assert_can_be_reached(route, route_args)

    def test_view_container_one_level_deep(self):
        route = "article:view-container"
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
            "container_slug": self.container.slug,
        }
        self.assert_can_be_reached(route, route_args)

    def test_view_container_two_level_deep(self):
        route = "article:view-container"
        route_args = {
            "pk": self.content.pk,
            "slug": self.content.slug,
            "parent_container_slug": self.container.slug,
            "container_slug": self.subcontainer.slug,
        }
        self.assert_can_be_reached(route, route_args)
