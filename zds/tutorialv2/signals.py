from django.dispatch.dispatcher import Signal

# Publication events
content_published = Signal(providing_args=["instance", "user", "by_email"])
content_unpublished = Signal(providing_args=["instance", "target", "moderator"])

content_read = Signal(providing_args=["instance", "user", "target"])
