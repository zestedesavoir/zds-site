from django.template import Context, Template, TemplateSyntaxError
from django.test import TestCase


class CaptureasNodeTest(TestCase):
    def setUp(self):
        self.context = Context()

    def test_valid_templatetag(self):
        # Test empty element
        self.assertFalse("var1" in self.context)
        tr = Template("{% load captureas %}" "{% captureas var1%}" "{% endcaptureas %}").render(self.context)
        self.assertTrue("var1" in self.context)

        self.assertEqual(tr, "")
        self.assertEqual(self.context["var1"], "")

        # Test simple content
        self.assertFalse("var2" in self.context)
        tr = Template(
            "{% load captureas %}"
            "{% captureas var2%}"
            "{% for i in 'xxxxxxxxxx' %}"
            "{{forloop.counter0}}"
            "{% endfor %}"
            "{% endcaptureas %}"
        ).render(self.context)
        self.assertTrue("var2" in self.context)

        self.assertEqual(tr, "")
        self.assertEqual(self.context["var2"], "0123456789")

    def test_invalid_templatetag(self):
        # No var name
        tp = "{% load captureas %}" "{% captureas%}" "{% endcaptureas %}"
        self.assertRaises(TemplateSyntaxError, Template, tp)

        # Too many var name
        tp = "{% load captureas %}" "{% captureas v1 v2%}" "{% endcaptureas %}"
        self.assertRaises(TemplateSyntaxError, Template, tp)
