from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.test import TestCase

from zds.member.models import Profile
from zds.member.tests.factories import ProfileFactory
from zds.utils.forms import TagValidator
from zds.utils.models import Hat, Tag


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
        tags = ["a", "b", "c"]
        insert_valid_tags(tags)
        tags_len += 3
        self.assertEqual(tags_len, len(Tag.objects.all()))

        # add duplicated tags
        tags = ["a", "b", "c"]
        insert_duplicated_tags(tags)
        self.assertEqual(tags_len, len(Tag.objects.all()))

        # add tags with invalid content
        tags = ["", " "]
        insert_invalid_tags(tags)

        self.assertEqual(
            tags_len,
            Tag.objects.count(),
            'all tags are "{}"'.format('","'.join(Tag.objects.values_list("title", flat=True))),
        )

        # test tags title stripping
        tags = ["foo bar", "  azerty", "\u00A0qwerty ", " another tag "]
        insert_valid_tags(tags)

        all_titles = Tag.objects.values_list("title", flat=True)
        self.assertIn("foo bar", all_titles)
        self.assertIn("azerty", all_titles)
        self.assertIn("qwerty", all_titles)
        self.assertIn("another tag", all_titles)

        all_slugs = Tag.objects.values_list("slug", flat=True)
        self.assertIn("foo-bar", all_slugs)
        self.assertIn("azerty", all_slugs)
        self.assertIn("qwerty", all_slugs)
        self.assertIn("another-tag", all_slugs)

    def test_validator_with_correct_tags(self):
        tag = Tag(title="a test")
        tag.save()
        validator = TagValidator()
        self.assertEqual(validator.validate_raw_string(None), True)
        self.assertEqual(validator.validate_raw_string(tag.title), True)
        self.assertEqual(validator.errors, [])

    def test_validator_with_special_char_only(self):
        validator = TagValidator()
        self.assertFalse(validator.validate_raw_string("^"))
        self.assertEqual(len(validator.errors), 1)

    def test_validator_with_utf8mb4(self):
        raw_string = "🐙☢,bla"
        validator = TagValidator()
        self.assertFalse(validator.validate_raw_string(raw_string))
        self.assertEqual(1, len(validator.errors))

    def test_prevent_users_getting_hat_linked_to_group(self):
        # Create a hat and add it to a user
        hat_name = "Test hat"
        profile = ProfileFactory()
        hat, _ = Hat.objects.get_or_create(name__iexact=hat_name, defaults={"name": hat_name})
        profile.hats.add(hat)
        self.assertIn(hat_name, [h.name for h in profile.hats.all()])
        # Now, link a group to this hat
        group, _ = Group.objects.get_or_create(name="test_hat")
        hat.group = group
        hat.save()
        # The user shoudn't have the hat through their profile anymore
        profile = Profile.objects.get(pk=profile.pk)  # reload
        self.assertNotIn(hat, profile.hats.all())
