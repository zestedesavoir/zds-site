from django.dispatch import Signal

# is sent when a content is read (topic, article or tutorial)
# arguments: instance, user, target
content_read = Signal()
