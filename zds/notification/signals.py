from django.dispatch import Signal

# is sent whenever a resource is created.
new_content = Signal(providing_args=["instance", "user", "by_email"])

# is sent when a content is read (topic, article or tutorial)
content_read = Signal(providing_args=["instance", "user", "target"])

unsubscribe = Signal(providing_args=["instance", "user"])
