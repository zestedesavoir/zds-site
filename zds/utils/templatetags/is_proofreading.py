from django import template

register = template.Library()


@register.filter('is_proofreading')
def is_proofreading(content, user):
    """
    returns true if the user is a proofreader of the content
    :param content:
    :param user:
    :return:
    :rtype: bool
    """

    return user.pk in content.proofreaders.values_list('pk', flat=True)
