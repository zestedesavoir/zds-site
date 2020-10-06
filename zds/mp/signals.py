from django.dispatch import Signal

participant_added = Signal(providing_args=['instance'])
participant_removed = Signal(providing_args=['instance'])
