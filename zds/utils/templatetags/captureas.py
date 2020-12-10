from django import template
from django.utils.safestring import mark_safe

register = template.Library()

"""
Define a tag allowing to capture template content as a variable.
"""


@register.tag(name="captureas")
def do_captureas(parser, token):
    """
    Define a tag allowing to capture template content as a variable.

    :param parser: The django template parser
    :param token: tag token (tag_name + variable_name)
    :return: Template node.
    """

    try:
        _, variable_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")

    nodelist = parser.parse(("endcaptureas",))
    parser.delete_first_token()

    return CaptureasNode(nodelist, variable_name)


class CaptureasNode(template.Node):
    """
    Capture and render a nodelist to a new variable.
    """

    def __init__(self, nodelist, variable_name):
        """
        Create a template node which render `nodelist` to `variable_name`.

        :param nodelist: The node list to capture.
        :param variable_name: The variable name which will gain the rendered content.
        """
        self.__node_list = nodelist
        self.__variable_name = variable_name

    def render(self, context):
        """
        Render the node list to the variable name.

        :param context: Current context.
        :return: Empty string
        :rtype: str
        """
        output = self.__node_list.render(context)
        context[self.__variable_name] = mark_safe(output.strip())
        return ""
