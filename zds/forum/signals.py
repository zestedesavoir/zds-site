from django.dispatch import Signal

topic_moved = Signal(providing_args=['instance'])
topic_edited = Signal(providing_args=['instance'])
