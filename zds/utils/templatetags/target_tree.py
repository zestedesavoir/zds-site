from django import template

from zds.tutorialv2.models.versioned import Container, Extract
from zds.tutorialv2.utils import get_target_tagged_tree

register = template.Library()


@register.filter("target_tree")
def target_tree(child):
    """
    A django filter that wrap zds.tutorialv2.utils.get_target_tagged_tree function
    """
    if isinstance(child, Container):
        root = child.top_container()
    elif isinstance(child, Extract):
        root = child.container.top_container()
    return get_target_tagged_tree(child, root)
