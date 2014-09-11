# -*- coding: utf-8 -*-


from django.test import TestCase, RequestFactory
from django.template import TemplateSyntaxError, Token, TOKEN_TEXT, Context

from zds.utils.templatetags.append_to_get import easy_tag, AppendGetNode


class EasyTagTest(TestCase):
    def setUp(self):
        def my_function(a, b, c):
            """My doc string."""
            return a, b, c

        self.simple_function = my_function
        self.wrapped_function = easy_tag(self.simple_function)

    def test_valid_call(self):

        # Call tag without parser and three elements
        ret = self.wrapped_function(None, Token(TOKEN_TEXT, "elem1 elem2 elem3"))

        # Check arguments have been split
        self.assertEqual(3, len(ret))
        self.assertEqual("elem1", ret[0])
        self.assertEqual("elem2", ret[1])
        self.assertEqual("elem3", ret[2])

        # Check functions wrapping
        self.assertEqual(self.simple_function.__name__, self.wrapped_function.__name__)
        self.assertEqual(self.simple_function.__doc__, self.wrapped_function.__doc__)

    def test_invalid_call(self):

        # Check raising TemplateSyntaxError if call with too few arguments
        self.assertRaises(TemplateSyntaxError, self.wrapped_function, None, Token(TOKEN_TEXT,"elem1 elem2"))

        # Check raising TemplateSyntaxError if call with too many arguments
        self.assertRaises(TemplateSyntaxError, self.wrapped_function, None, Token(TOKEN_TEXT,"elem1 elem2 elem3 elem4"))


class AppendGetNodeTest(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        factory = RequestFactory()
        self.argl1 = "key1=var1"

        self.argl2 = "key1=var1,key2=var2"
        self.context = Context({'request': factory.get('/data/test'), 'var1': 1, 'var2': 2})

    def test_valid_call(self):

        # Test normal call
        agn = AppendGetNode(self.argl2)
        tr = agn.render(self.context)
        self.assertTrue(tr == "/data/test?key1=1&key2=2" or tr == "/data/test?key2=2&key1=1")

        # Test call with one argument
        agn = AppendGetNode(self.argl1)
        tr = agn.render(self.context)
        self.assertEqual(tr, "/data/test?key1=1")


        # Test call without arguments
        agn = AppendGetNode("")
        tr = agn.render(self.context)
        self.assertEqual(tr, "/data/test")


