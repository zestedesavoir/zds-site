from django.dispatch import Signal

# argument: topic
topic_moved = Signal()

# argument: topic
topic_edited = Signal()

# arguments: instance, user
topic_read = Signal()

# arguments: instance, user
post_read = Signal()

# arguments: post, user
post_unread = Signal()
