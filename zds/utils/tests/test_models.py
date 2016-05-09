from django.test import TestCase

from zds.utils.models import Tag


class TestTags(TestCase):

    def test_get_tags_by_title(self):
        tag1 = Tag.objects.get_from_title("aaa")
        tag2 = Tag.objects.get_from_title("aaa")
        tag3 = Tag.objects.get_from_title("bbb")
        tag4 = Tag.objects.get_from_title("b" * Tag._meta.get_field("title").max_length + "c")
        tag5 = Tag.objects.get_from_title("b" * Tag._meta.get_field("title").max_length + "c")
        tag6 = Tag.objects.get_from_title("b" * Tag._meta.get_field("title").max_length)
        self.assertEqual(tag1.pk, tag2.pk)
        self.assertEqual(tag4.pk, tag5.pk)
        self.assertEqual(tag5.pk, tag6.pk)
