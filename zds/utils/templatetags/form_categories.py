from django import template

from zds.utils.models import SubCategory

register = template.Library()


@register.filter("order_categories")
def order_categories(choices):
    """
    This is a special templatetag used in "new content" page to diplay all categories in the right order.
    We use it because Django Crispy Form have not yet this functionality.
    Only used in `templates/crispy/checkboxselectmultiple.html`.
    :param choices:
    :return:
    """
    new_choices = []
    for choice in choices:
        # many request but only used in "new content" page
        # if someone find a better solution, please create a Pull Request
        subcat = SubCategory.objects.get(pk=choice[0].value)
        parent = subcat.get_parent_category()
        if parent:
            ch = {"choice": choice, "parent": parent.title, "order": parent.pk}
            new_choices.append(ch)
    return new_choices
