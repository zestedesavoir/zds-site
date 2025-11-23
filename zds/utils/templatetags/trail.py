import re

from django import template

register = template.Library()

tag_regexp = re.compile(r">\s+<")
breaks_regexp = re.compile(r"[\n\r\f\v]+")
spaces_line_begin_regexp = re.compile(r"^[ \t]+", flags=re.MULTILINE)
spaces_line_end_regexp = re.compile(r"[ \t]+$", flags=re.MULTILINE)

"""
Define a tag to remove trailing whitespaces
"""


@register.tag(name="trail")
def do_trail(parser, token):
    """
    Define a tag to remove trailing whitespaces between tags and between tags and text

    :param parser: The django template parser
    :param token: tag token (tag_name + variable_name)
    :return: Template node.
    """

    nodelist = parser.parse(("endtrail",))
    parser.delete_first_token()
    return TrailNode(nodelist)


class TrailNode(template.Node):
    """
    Remove spaces between tags, before and after newlines and newlines
    """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        new_text = tag_regexp.sub("><", self.nodelist.render(context))
        new_text = spaces_line_begin_regexp.sub("", new_text)
        new_text = spaces_line_end_regexp.sub("", new_text)
        new_text = breaks_regexp.sub(" ", new_text)
        return new_text
