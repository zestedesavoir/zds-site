# -*- coding: utf-8 -*-
from django.dispatch import Signal


# is sent whenever an answer is set as unread
answer_unread = Signal(providing_args=["instance", "user"])

# is sent when a content is read (topic, article or tutorial)
content_read = Signal(providing_args=["instance", "user"])
