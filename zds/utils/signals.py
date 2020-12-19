from django.dispatch import Signal

ping = Signal(providing_args=["instance", "user", "by_email"])
unping = Signal(providing_args=["instance", "user"])
