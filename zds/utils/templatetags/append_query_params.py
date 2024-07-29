from functools import wraps
from urllib.parse import quote

from django import template

register = template.Library()

"""
Decorator to facilitate template tag creation.
"""


def easy_tag(func):
    """
    Deal with the repetitive parts of parsing template tags :

     - Wraps functions attributes;
     - Raise `TemplateSyntaxError` if arguments are not well formatted.

    :rtype: function
    :param func: Function to wraps.
    :type func: function
    """

    @wraps(func)
    def inner(_, token):
        split_arg = token.split_contents()
        try:
            return func(*split_arg)
        except TypeError:
            import inspect

            args = inspect.getfullargspec(func).args[1:]

            err_msg = 'Bad arguments for tag "{0}".\nThe tag "{0}" take {1} arguments ({2}).\n {3} were provided ({4}).'
            fstring = err_msg.format(split_arg[0], len(args), ", ".join(args), len(split_arg), ", ".join(split_arg))
            raise template.TemplateSyntaxError(fstring)

    return inner


class AppendGetNode(template.Node):
    """
    Template node allowing to render an URL appending argument to current GET address.

    Parse a string like `key1=var1,key2=var2` and generate a new URL with the provided parameters appended to current
    parameters.
    """

    def __init__(self, arg_list):
        """
        Create a template node which append `arg_list` to GET URL.

        :param str arg_list: the argument list to append.
        """

        self.__dict_pairs = {}
        for pair in arg_list.split(","):
            if pair:
                try:
                    key, val = pair.split("=")
                    if not val:
                        raise template.TemplateSyntaxError(f"Bad argument format. Empty value for key '{key}")
                    self.__dict_pairs[key] = template.Variable(val)
                except ValueError:
                    raise template.TemplateSyntaxError(
                        f"Bad argument format.\n'{arg_list}' must use the format 'key1=var1,key2=var2'"
                    )

    def render(self, context):
        """
        Render the new URL according to the current context.

        :param context: Current context.
        :return: New URL with arguments appended.
        :rtype: str
        """
        get = context["request"].GET.copy()
        path = context["request"].META["PATH_INFO"]

        for key in self.__dict_pairs:
            get[key] = self.__dict_pairs[key].resolve(context)

        if len(get) > 0:
            list_arg = [f"{key}={quote(str(value))}" for key in list(get.keys()) for value in get.getlist(key)]
            path += "?" + "&".join(list_arg)

        return path


@register.tag()
@easy_tag
def append_query_params(_, arg_list):
    """Render an URL appending argument to current GET address.

    :param _: Tag name (not used)
    :param arg_list: Argument list like `key1=var1,key2=var2`
    :return: Template node.
    """
    return AppendGetNode(arg_list)
