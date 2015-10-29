from django import template

from zds.search import MODEL_NAMES

register = template.Library()


@register.tag(name="model_name")
def do_model_name(parser, token):
    try:
        tag_name, app_label, model_name, plural = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires three arguments" % token.contents.split()[0])
    return ModelNameNode(app_label, model_name, plural)


class ModelNameNode(template.Node):

    def __init__(self, app_label, model_name, plural):
        self.app_label = template.Variable(app_label)
        self.model_name = template.Variable(model_name)
        self.plural = template.Variable(plural)

    def render(self, context):
        try:
            app_label = self.app_label.resolve(context)
            model_name = self.model_name.resolve(context)
            plural = self.plural.resolve(context)
            return MODEL_NAMES[app_label][model_name][plural]
        except template.VariableDoesNotExist:
            return ''
