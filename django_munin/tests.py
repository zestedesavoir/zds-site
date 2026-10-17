from django.test import RequestFactory, TestCase

from django_munin.munin.helpers import muninview


class MuninViewDecoratorTests(TestCase):
    # These tests doesn't require a database, tell it to Django, to skip the
    # creation of test database and speed-up test initialisation.
    databases = {}

    def test_autoconfig(self):
        config = "graph_title Total Topics\ngraph_vlabel topics"

        @muninview(config=config)
        def view(request):
            return [("topics", 12), ("solved", 2)]

        request = RequestFactory().get("/munin/view", {"autoconfig": 1})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "yes")

    def test_default_labels(self):
        config = "graph_title Total Topics\ngraph_vlabel topics"

        @muninview(config=config)
        def view(request):
            return [("topics", 12), ("solved", 2)]

        request = RequestFactory().get("/munin/view")
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "topics 12\nsolved 2")

        request = RequestFactory().get("/munin/view", {"config": 1})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), f"{config}\ntopics.label topics\nsolved.label solved")

    def test_custom_labels(self):
        config = """graph_title Total Posts
graph_vlabel posts
posts.label Forum posts
posts.draw LINE1
comments.label Article and Tutorial comments
comments.draw STACK"""

        @muninview(config=config)
        def view(request):
            return [("posts", 12), ("comments", 2)]

        request = RequestFactory().get("/munin/view")
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "posts 12\ncomments 2")

        request = RequestFactory().get("/munin/view", {"config": 1})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), config)
