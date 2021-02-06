from django.dispatch import Signal

topic_moved = Signal(providing_args=["topic"])
topic_edited = Signal(providing_args=["topic"])
topic_read = Signal(providing_args=["instance", "user"])
post_read = Signal(providing_args=["instance", "user"])
post_unread = Signal(providing_args=["post", "user"])
