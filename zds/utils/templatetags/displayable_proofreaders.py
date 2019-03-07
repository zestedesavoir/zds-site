from django import template

register = template.Library()


@register.filter('displayable_proofreaders')
def displayable_proofreaders(content):
    """
    gets an iterable over the proofreaders attached to the current displayed version.
    :param content:
    :return:
    :rtype: iterable[zds.members.models.User]
    """
    return content.proofreaders.all()
