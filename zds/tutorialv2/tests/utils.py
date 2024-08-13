from zds.tutorialv2.tests.factories import ValidationFactory


def request_validation(content):
    """Emulate a proper validation request."""
    ValidationFactory(content=content, status="PENDING")
    content.sha_validation = content.sha_draft
    content.save()
