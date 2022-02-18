from django.dispatch.dispatcher import Signal

# Display management
content_read = Signal(providing_args=["instance", "user", "target"])

# Publication events
content_published = Signal(providing_args=["instance", "user", "by_email"])
content_unpublished = Signal(providing_args=["instance", "target", "moderator"])

# Authors management
# For the signal below, the arguments "performer", "content", "author" and "action" shall be provided.
# Action is either "add" or "remove".
authors_management = Signal()

# Contributors management
# For the signal below, the arguments "performer", "content", "contributor" and "action" shall be provided.
# Action is either "add" or "remove".
contributors_management = Signal()

# Beta management
# For the signal below, the arguments "performer", "content", "version" and "action" shall be provided.
# Action is either "activate" or "deactivate".
beta_management = Signal()

# Validation management
# For the signal below, the arguments "performer", "content", "version" and "action" shall be provided.
# Action is either "request", "cancel", "accept", "reject", "revoke", "reserve" or "unreserve".
validation_management = Signal()

# Tags management
# For the signal below, the arguments "performer" and "content"  shall be provided.
tags_management = Signal()

# Suggestions management
# For the signal below, the arguments "performer" and "content"  shall be provided.
# Action is either "add" or "remove".
suggestions_management = Signal()

# Help management
# For the signal below, the arguments "performer" and "content"  shall be provided.
help_management = Signal()

# JSFiddle management
# For the signal below, the arguments "performer", "content" and "action" shall be provided.
# Action is either "activate" or "deactivate".
jsfiddle_management = Signal()

# Opinion publication management
# For the signal below, the arguments "performer", "content" and "action" shall be provided.
# Action is either "publish" or "unpublish".
opinions_management = Signal()
