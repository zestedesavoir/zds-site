from django.template.defaulttags import register


@register.filter(name="get_tuple_item")
def get_tuple_item(dictionary, index):
    return dictionary[index]
