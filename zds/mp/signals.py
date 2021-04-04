from django.dispatch import Signal

# New message management
message_added = Signal()  # providing_args=["post", "by_email", "no_notification_for"]

# Read/Unread management
topic_read = Signal()  # providing_args=["instance", "user"]
message_unread = Signal()  # providing_args=["instance", "user"]

# Participant management
participant_added = Signal()  # providing_args=["topic", "silent"]
participant_removed = Signal()  # providing_args=["topic"]

topic_created = Signal()  # providing_args=["topic", "by_email"]
