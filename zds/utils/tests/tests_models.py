# coding: utf-8
from django.test import TestCase
from django.db import IntegrityError, transaction

from zds.utils.models import Tag


class TagsTests(TestCase):
    def test_tags(self):
        def insert_valid_tags(tags):
            for tag in tags:
                Tag(title=tag).save()

        def insert_invalid_tags(tags):
            for tag in tags:
                with self.assertRaises(ValueError):
                    Tag(title=tag).save()

        def insert_duplicated_tags(tags):
            for tag in tags:
                dupe = Tag(title=tag)
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        dupe.save()

        tags_len = len(Tag.objects.all())

        # add 3 tags
        tags = ['a', 'b', 'c']
        insert_valid_tags(tags)
        tags_len += 3
        self.assertEqual(tags_len, len(Tag.objects.all()))

        # add duplicated tags
        tags = ['a', 'b', 'c']
        insert_duplicated_tags(tags)
        self.assertEqual(tags_len, len(Tag.objects.all()))

        # add tags with invalid content
        tags = ['', ' ']
        insert_invalid_tags(tags)

        self.assertEqual(tags_len, Tag.objects.count(),
                         'all tags are "{}"'.format('","'.join(Tag.objects.values_list('title', flat=True))))

        # test tags title stripping
        tags = ['foo bar', '  azerty', u'\u00A0qwerty ', ' another tag ']
        insert_valid_tags(tags)

        all_titles = Tag.objects.values_list('title', flat=True)
        self.assertIn('foo bar', all_titles)
        self.assertIn('azerty', all_titles)
        self.assertIn('qwerty', all_titles)
        self.assertIn('another tag', all_titles)

        all_slugs = Tag.objects.values_list('slug', flat=True)
        self.assertIn('foo-bar', all_slugs)
        self.assertIn('azerty', all_slugs)
        self.assertIn('qwerty', all_slugs)
        self.assertIn('another-tag', all_slugs)
