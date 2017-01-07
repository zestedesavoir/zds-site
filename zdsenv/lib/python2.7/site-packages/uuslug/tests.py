# -*- coding: utf-8 -*-

from django.test import TestCase

# http://pypi.python.org/pypi/django-tools/
# from django_tools.unittest_utils.print_sql import PrintQueries

from uuslug import slugify
from uuslug.models import (CoolSlug, AnotherSlug, TruncatedSlug,
                           SmartTruncatedSlug, SmartTruncatedExactWordBoundrySlug,
                           CoolSlugDifferentSeparator, TruncatedSlugDifferentSeparator)


class SlugUnicodeTestCase(TestCase):
    """Tests for Slug - Unicode"""

    def test_manager(self):

        txt = "This is a test ---"
        r = slugify(txt)
        self.assertEqual(r, "this-is-a-test")

        txt = "This -- is a ## test ---"
        r = slugify(txt)
        self.assertEqual(r, "this-is-a-test")

        txt = '影師嗎'
        r = slugify(txt)
        self.assertEqual(r, "ying-shi-ma")

        txt = 'C\'est déjà l\'été.'
        r = slugify(txt)
        self.assertEqual(r, "cest-deja-lete")

        txt = 'Nín hǎo. Wǒ shì zhōng guó rén'
        r = slugify(txt)
        self.assertEqual(r, "nin-hao-wo-shi-zhong-guo-ren")

        txt = 'Компьютер'
        r = slugify(txt)
        self.assertEqual(r, "kompiuter")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt)
        self.assertEqual(r, "jaja-lol-mememeoo-a")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=9)
        self.assertEqual(r, "jaja-lol")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=15)
        self.assertEqual(r, "jaja-lol-mememe")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=50)
        self.assertEqual(r, "jaja-lol-mememeoo-a")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=15, word_boundary=True)
        self.assertEqual(r, "jaja-lol-a")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=19, word_boundary=True)
        self.assertEqual(r, "jaja-lol-mememeoo")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=20, word_boundary=True)
        self.assertEqual(r, "jaja-lol-mememeoo-a")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=20, word_boundary=True, separator=".")
        self.assertEqual(r, "jaja.lol.mememeoo.a")

        txt = 'jaja---lol-méméméoo--a'
        r = slugify(txt, max_length=20, word_boundary=True, separator="ZZZZZZ")
        self.assertEqual(r, "jajaZZZZZZlolZZZZZZmememeooZZZZZZa")

        txt = "___This is a test ---"
        r = slugify(txt)
        self.assertEqual(r, "this-is-a-test")

        txt = "___This is a test___"
        r = slugify(txt)
        self.assertEqual(r, "this-is-a-test")


class SlugUniqueTestCase(TestCase):
    """Tests for Slug - Unique"""

    def test_manager(self):
        name = "john"

        # with PrintQueries("create first john"): # display the SQL queries
        with self.assertNumQueries(2):
            # 1. query: SELECT test, if slug 'john' exists
            # 2. query: INSERT values
            obj = CoolSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "john")

        # with PrintQueries("create second john"): # display the SQL queries
        with self.assertNumQueries(3):
            # 1. query: SELECT test, if slug 'john' exists
            # 2. query: SELECT test, if slug 'john-1' exists
            # 3. query: INSERT values
            obj = CoolSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "john-1")

    def test_start_no(self):
        name = 'Foo Bar'

        # with PrintQueries("create first 'Foo Bar'"): # display the SQL queries
        with self.assertNumQueries(2):
            # 1. query: SELECT test, if slug 'foo-bar' exists
            # 2. query: INSERT values
            obj = AnotherSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "foo-bar")

        # with PrintQueries("create second 'Foo Bar'"): # display the SQL queries
        with self.assertNumQueries(3):
            # 1. query: SELECT test, if slug 'foo-bar' exists
            # 2. query: SELECT test, if slug 'foo-bar-2' exists
            # 3. query: INSERT values
            obj = AnotherSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "foo-bar-2")

        # with PrintQueries("create third 'Foo Bar'"): # display the SQL queries
        with self.assertNumQueries(4):
            # 1. query: SELECT test, if slug 'foo-bar' exists
            # 2. query: SELECT test, if slug 'foo-bar-2' exists
            # 3. query: SELECT test, if slug 'foo-bar-3' exists
            # 4. query: INSERT values
            obj = AnotherSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "foo-bar-3")

    def test_max_length(self):
        name = 'jaja---lol-méméméoo--a'

        obj = TruncatedSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja-lol-mememeoo")  # 17 is max_length

        obj = TruncatedSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja-lol-mememe-2")  # 17 is max_length

        obj = TruncatedSlug.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja-lol-mememe-3")  # 17 is max_length

    def test_max_length_exact_word_boundry(self):
        name = 'jaja---lol-méméméoo--a'

        obj = SmartTruncatedExactWordBoundrySlug.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja-lol-mememeoo")  # 19 is max_length

        obj = SmartTruncatedExactWordBoundrySlug.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja-lol-mememeoo-9")  # 19 is max_length, start_no = 9

        obj = SmartTruncatedExactWordBoundrySlug.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja-lol-mememeo-10")  # 19 is max_length, readjust for "-10"


class SlugUniqueDifferentSeparatorTestCase(TestCase):
    """Tests for Slug - Unique with different separator """

    def test_manager(self):
        name = "john"

        # with PrintQueries("create first john"): # display the SQL queries
        with self.assertNumQueries(2):
            # 1. query: SELECT test, if slug 'john' exists
            # 2. query: INSERT values
            obj = CoolSlugDifferentSeparator.objects.create(name=name)
        self.assertEqual(obj.slug, "john")

        # with PrintQueries("create second john"): # display the SQL queries
        with self.assertNumQueries(3):
            # 1. query: SELECT test, if slug 'john' exists
            # 2. query: SELECT test, if slug 'john-1' exists
            # 3. query: INSERT values
            obj = CoolSlugDifferentSeparator.objects.create(name=name)
        self.assertEqual(obj.slug, "john_1")

        # with PrintQueries("create third john"): # display the SQL queries
        with self.assertNumQueries(4):
            # 1. query: SELECT test, if slug 'john' exists
            # 2. query: SELECT test, if slug 'john-1' exists
            # 3. query: INSERT values
            obj = CoolSlugDifferentSeparator.objects.create(name=name)
        self.assertEqual(obj.slug, "john_2")

    def test_max_length(self):
        name = 'jaja---lol-méméméoo--a'

        obj = TruncatedSlugDifferentSeparator.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja_lol_mememeoo")  # 17 is max_length

        obj = TruncatedSlugDifferentSeparator.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja_lol_mememe_2")  # 17 is max_length

        obj = TruncatedSlugDifferentSeparator.objects.create(name=name)
        self.assertEqual(obj.slug, "jaja_lol_mememe_3")  # 17 is max_length
