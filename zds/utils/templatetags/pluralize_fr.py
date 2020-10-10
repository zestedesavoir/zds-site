from django import template

register = template.Library()


@register.filter(is_safe=False)
def pluralize_fr(value, arg="s"):
    """
    Based on default pluralize filter : https://github.com/django/django/blob/master/django/template/defaultfilters.py
    Support french (-1, 0 and 1 are singular).
    """
    if "," not in arg:
        arg = "," + arg
    bits = arg.split(",")
    if len(bits) > 2:
        return ""
    singular_suffix, plural_suffix = bits[:2]

    try:
        if not (-2 < float(value) < 2):
            return plural_suffix
    except ValueError:  # Invalid string that's not a number.
        pass
    except TypeError:  # Value isn't a string or a number; maybe it's a list?
        try:
            if not (-2 < len(value) < 2):
                return plural_suffix
        except TypeError:  # len() of unsized object.
            pass
    return singular_suffix
