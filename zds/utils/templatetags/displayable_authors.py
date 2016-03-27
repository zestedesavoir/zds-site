from django import template

register = template.Library()


@register.filter("displayable_authors")
def displayable_authors(content, online):
    """
    gets an iterable over the authors attached to the current displayed version.
    if version is public we only want the authors that participated to the published version redaction
    otherwise all current authors (event those who were added and without those who were removed) are given
    :param content:
    :param online:
    :return:
    :rtype: iterable[zds.members.models.User]
    """
    if online:
        return content.public_version.authors.all()
    return content.authors.all()
