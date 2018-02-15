import re

from django import template

register = template.Library()

html_tag = re.compile(r'<.*?>')


def format_highlight(highlighted_fragments):
    """Strip HTML, then transform back into html with highlighted fragments only.

    :param highlighted_fragments: list of fragments from elasticsearch
    :type highlighted_fragments: list
    :return: the formatted string
    :rtype: str
    """

    fragments = []
    for fragment in highlighted_fragments:
        if fragment:
            fragments.append(
                html_tag.sub('', fragment).replace('[hl]', '<mark class="highlighted">').replace('[/hl]', '</mark>'))

    return ' &hellip; '.join(fragments)


class HighlightNode(template.Node):
    """For a elasticsearch result, looks into ``.meta.highlight`` if something has been highlighted. If so, use that
    information. Otherwise, just give back the text.

    See https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-highlighting.html

    Note that the class expects ``"pre_tags" : ["[hl]"], "post_tags" : ["[/hl]"]``, since all HTML is stripped.
    """

    def __init__(self, search_result, field):
        self.search_result = search_result
        self.field = field

    def render(self, context):
        search_result = context[self.search_result]

        if self.field[0] in ['"', "'"]:
            field = self.field[1:-1]
        else:
            field = template.Variable(self.field).resolve(context)

        if field not in search_result:
            raise template.VariableDoesNotExist('field {} is not a member of the search result'.format(field))

        text = ''

        if search_result[field]:
            text = html_tag.sub('', search_result[field])

        if 'highlight' in search_result.meta:
            if field in search_result.meta.highlight:
                text = format_highlight(search_result.meta.highlight[field])

        return text


@register.tag
def highlight(parser, token):

    part = token.split_contents()

    if len(part) != 3:
        raise template.TemplateSyntaxError(
            "'highlight' tag must be of the form:  {% highlight <search_result> <field> %}")

    return HighlightNode(part[1], part[2])
