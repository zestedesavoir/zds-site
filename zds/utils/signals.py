from django.dispatch import Signal

# arguments: instance, user, by_email
ping = Signal()

# arguments: instance, user
unping = Signal()
