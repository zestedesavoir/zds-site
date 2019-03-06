from django import template

register = template.Library()


@register.filter('is_testing')
def is_testing(content, user):
    """
    returns true if the user is a tester of the content
    :param content:
    :param user:
    :return:
    :rtype: bool
    """

    return user.pk in content.testers.values_list('pk', flat=True)
