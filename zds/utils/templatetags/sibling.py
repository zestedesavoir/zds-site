from django import template

register = template.Library()


@register.tag(name='sibling')
def do_sibling(parser, token):
    """
    Parse : sibling {list} {dir} [as {ouput_name}]

    :param parser: The django template parser
    :param token: tag token (tag_name + variable_name)
    :return: Template node.
    """
    try:
        if len(token.split_contents()) == 3:  # Parse : sibling {list} {dir}
            tag_name, variable_name, direction = token.split_contents()
            as_word = 'as'
            output_name = (direction, 'current')[direction.isdigit()]
            """
            if {dir} is digit, the parser understands :
                `sibling {list} {dir} as current`
            else, it understands :
                `sibling {list} {dir} as {dir}`
            """
        else:  # Parse : sibling {list} {dir} as {ouput_name}
            tag_name, variable_name, direction, as_word, output_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            'sibling tag requires exactly two or third arguments : sibling {list} {dir} [as {ouput_name}]'
        )

    if direction not in ('prev', 'next') and not direction.isdigit():
        raise template.TemplateSyntaxError(
            'sibling tag requires 2nd argument equal to `prev` or `next` instead of %r.' % direction
        )

    if as_word != 'as':
        raise template.TemplateSyntaxError(
            'Invalid syntax in sibling tag. Expecting `as` keyword instead of %r.' % as_word
        )

    return SiblingNode(variable_name, direction, output_name)


class SiblingNode(template.Node):
    """
    Set the selected element, next element or prev element of {list} in {ouput_name} variable.

    sibling {list} {dir} [as {ouput_name}]
    """
    def __init__(self, variable_name, direction, output_name):
        """
        Render the node list to the variable name.
        :param variable_name: The list contains values to get.
        :param direction: The key or the selector to get the selected value in {variable_name} list.
        :param output_name: The output variable contains the value returned.
        """
        self.variable_name = variable_name
        self.direction = direction
        self.output_name = output_name

    def render(self, context):
        """
        Set {output_name} variable with selected element of {variable_name} according to {direction}.
        :param context: Current context.
        :return: Empty string
        :rtype: str
        """
        counter0 = 0
        currentlist = template.Variable(self.variable_name).resolve(context)

        if self.direction.isdigit():
            counter0 = self.direction
            side = 0
        else:
            if self.direction == 'next':
                side = 1
            else:  # self.direction == prev
                side = -1

            if 'siblingStep' in context:
                counter0 = context['siblingStep']
            elif 'forloop' in context and 'counter0' in context['forloop']:  # get loop count
                counter0 = context['forloop']['counter0']
            elif self.direction == 'prev':  # not in a loop and prev dir, we start at the end
                counter0 = len(currentlist) - 1

        try:
            sibling = currentlist[int(counter0) + side]
        except:
            sibling = {}

        context[self.output_name] = sibling
        return ''
