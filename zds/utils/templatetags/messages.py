from django import template

register = template.Library()

"""
Define a tag allowing to print properly all messages sent to the user.
"""


@register.inclusion_tag("messages.html", name="messages")
def messages(messages):
    """
    Define a tag allowing to print properly all messages sent to the user.

    :param messages: The messages list
    :return: dict
    """

    simple_messages = []
    for message in messages:
        simple_message = {"tags": str(message.tags), "text": str(message)}
        if simple_message["text"].startswith("['") and simple_message["text"].endswith("']"):
            simple_message["text"] = simple_message["text"][2:-2]
        simple_messages.append(simple_message)

    return {"messages": simple_messages}
