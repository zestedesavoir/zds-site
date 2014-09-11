from django import template

register = template.Library()


@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, variable_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")

    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()

    return CaptureasNode(nodelist, variable_name)


class CaptureasNode(template.Node):

    def __init__(self, nodelist, variable_name):
        self.__node_list = nodelist
        self.__variable_name = variable_name

    def render(self, context):
        output = self.__node_list.render(context)
        context[self.__variable_name] = output.strip(' \t\n\r')
        return ''
