from django.dispatch import Signal

# New message management
message_added = Signal(providing_args=['instance', 'user', 'by_email'])

# Read/Unread management
topic_read = Signal(providing_args=['instance', 'user', 'target'])
message_unread = Signal(providing_args=['instance', 'user'])

# Participant management
participant_added = Signal(providing_args=['instance'])
participant_removed = Signal(providing_args=['instance'])
