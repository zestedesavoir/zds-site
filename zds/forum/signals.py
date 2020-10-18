from django.dispatch import Signal

topic_moved = Signal(providing_args=['instance'])
