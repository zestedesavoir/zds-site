from django import template

register = template.Library()

"""
Decorator to facilitate template tag creation
"""


def easy_tag(func):
    """deal with the repetitive parts of parsing template tags"""
    def inner(parser, token):
        try:
            return func(*token.split_contents())
        except TypeError:
            raise template.TemplateSyntaxError('Bad arguments for tag "%s"' % token.split_contents()[0])
    inner.__name__ = func.__name__
    inner.__doc__ = inner.__doc__
    return inner


class AppendGetNode(template.Node):

    def __init__(self, dict):
        self.dict_pairs = {}
        for pair in dict.split(','):
            pair = pair.split('=')
            self.dict_pairs[pair[0]] = template.Variable(pair[1])

    def render(self, context):
        get = context['request'].GET.copy()
        path = context['request'].META['PATH_INFO']

        for key in self.dict_pairs:
            get[key] = self.dict_pairs[key].resolve(context)

        if len(get):
            path += "?"
            for (key, v) in get.items():
                for value in get.getlist(key):
                    path += u"&{0}={1}".format(key, value)

        return path


@register.tag()
@easy_tag
def append_to_get(_tag_name, dict):
    return AppendGetNode(dict)
