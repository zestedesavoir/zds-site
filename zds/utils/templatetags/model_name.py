from django import template
from zds.search.constants import MODEL_NAMES

register = template.Library()

@register.simple_tag(name="model_name")
def do_model_name(app_label, model_name, plural=False):
    return ModelNameNode(app_label, model_name, plural)


class ModelNameNode(template.Node):
    def __init__(self, app_label, model_name, plural):
        self.app_label = app_label
        self.model_name = model_name
        self.plural = plural
    def render(self, context):
        return MODEL_NAMES[self.app_label][self.model_name][self.plural];
