from django.dispatch.dispatcher import Signal

# is sent whenever a content is unpublished
content_unpublished = Signal(providing_args=['instance', 'target', 'moderator'])
