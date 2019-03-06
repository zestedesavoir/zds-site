from django import template

register = template.Library()


@register.filter('displayable_testers')
def displayable_testers(content):
    """
    gets an iterable over the testers attached to the current displayed version.
    :param content:
    :return:
    :rtype: iterable[zds.members.models.User]
    """
    return content.testers.all()
