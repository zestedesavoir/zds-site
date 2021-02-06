from django.dispatch import Signal

# is sent when a content is read (topic, article or tutorial)
content_read = Signal(providing_args=["instance", "user", "target"])
