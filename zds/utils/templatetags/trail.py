import re
from django import template

register = template.Library()

"""
Define a tag to remove trailing whitespaces
"""

@register.tag(name='trail')
def do_trail(parser, token):
    """
    Define a tag to remove trailing whitespaces between tags and between tags and text

    :param parser: The django template parser
    :param token: tag token (tag_name + variable_name)
    :return: Template node.
    """

    nodelist = parser.parse(('endtrail',))
    parser.delete_first_token()
    return TrailNode(nodelist)

class TrailNode(template.Node):
    """
    Removes all spaces between tags, removes newlines and replaces large spaces and tabs by a single space or tab respectively
    """
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        str = re.sub(r'>\s+<', '><', self.nodelist.render(context))
        str = re.sub(r'[\n\r\f\v]+', '', str)
        str = re.sub(r' +', ' ', str)
        str = re.sub(r'\t+', '\t', str)
        return str
