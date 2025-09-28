from django.template import Context, Template, TemplateSyntaxError, VariableDoesNotExist
from django.template.base import Token, TokenType
from django.test import RequestFactory, TestCase

from zds.utils.templatetags.append_query_params import AppendGetNode, easy_tag


class EasyTagTest(TestCase):
    def setUp(self):
        def my_function(a, b, c):
            """My doc string."""
            return a, b, c

        self.simple_function = my_function
        self.wrapped_function = easy_tag(self.simple_function)

    def test_valid_call(self):
        # Call tag without parser and three elements
        ret = self.wrapped_function(None, Token(TokenType.TEXT, "elem1 elem2 elem3"))

        # Check arguments have been split
        self.assertEqual(3, len(ret))
        self.assertEqual("elem1", ret[0])
        self.assertEqual("elem2", ret[1])
        self.assertEqual("elem3", ret[2])

        # Check functions wrapping
        self.assertEqual(self.simple_function.__name__, self.wrapped_function.__name__)
        self.assertEqual(self.simple_function.__doc__, self.wrapped_function.__doc__)

    def test_invalid_call(self):
        wf = self.wrapped_function
        # Check raising TemplateSyntaxError if call with too few arguments
        self.assertRaises(TemplateSyntaxError, wf, None, Token(TokenType.TEXT, "elem1 elem2"))

        # Check raising TemplateSyntaxError if call with too many arguments
        self.assertRaises(TemplateSyntaxError, wf, None, Token(TokenType.TEXT, "elem1 elem2 elem3 elem4"))


class AppendGetNodeTest(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        factory = RequestFactory()

        self.context = Context({"request": factory.get("/data/test"), "var1": 1, "var2": 2})

    def test_valid_call(self):
        # Test normal call
        agn = AppendGetNode("key1=var1,key2=var2")
        tr = agn.render(self.context)
        self.assertTrue(tr == "/data/test?key1=1&key2=2" or tr == "/data/test?key2=2&key1=1")

        # Test call with one argument
        agn = AppendGetNode("key1=var1")
        tr = agn.render(self.context)
        self.assertEqual(tr, "/data/test?key1=1")

        # Test call without arguments
        agn = AppendGetNode("")
        tr = agn.render(self.context)
        self.assertEqual(tr, "/data/test")

    def test_invalid_call(self):
        # Test invalid format

        # Space separators args :
        self.assertRaises(TemplateSyntaxError, AppendGetNode, "key1=var1 key2=var2")
        # No values :
        self.assertRaises(TemplateSyntaxError, AppendGetNode, "key1=,key2=var2")
        self.assertRaises(TemplateSyntaxError, AppendGetNode, "key1,key2=var2")
        # Not resolvable variable
        agn = AppendGetNode("key1=var3,key2=var2")
        self.assertRaises(VariableDoesNotExist, agn.render, self.context)

    def test_valid_templatetag(self):
        # Test normal call
        tr = Template("{% load append_query_params %}" "{% append_query_params key1=var1,key2=var2 %}").render(
            self.context
        )
        self.assertTrue(tr == "/data/test?key1=1&key2=2" or tr == "/data/test?key2=2&key1=1")

        # Test call with one argument
        tr = Template("{% load append_query_params %}" "{% append_query_params key1=var1 %}").render(self.context)
        self.assertEqual(tr, "/data/test?key1=1")

    def test_invalid_templatetag(self):
        # Test invalid format

        # Space separators args :
        str_tp = "{% load append_query_params %}" "{% append_query_params key1=var1 key2=var2 %}"
        self.assertRaises(TemplateSyntaxError, Template, str_tp)

        # No values :
        str_tp = "{% load append_query_params %}" "{% append_query_params key1=,key2=var2 %}"
        self.assertRaises(TemplateSyntaxError, Template, str_tp)
        str_tp = "{% load append_query_params %}" "{% append_query_params key1,key2=var2 %}"
        self.assertRaises(TemplateSyntaxError, Template, str_tp)

        # Not resolvable variable
        tr = Template("{% load append_query_params %}" "{% append_query_params key1=var3,key2=var2 %}")
        self.assertRaises(VariableDoesNotExist, tr.render, self.context)
