from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver

from zds.tutorialv2 import signals
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.views.authors import AddAuthorToContent, RemoveAuthorFromContent
from zds.tutorialv2.views.beta import ManageBetaContent
from zds.tutorialv2.views.canonical import EditCanonicalLinkView
from zds.tutorialv2.views.contributors import AddContributorToContent, RemoveContributorFromContent
from zds.tutorialv2.views.goals import EditGoals
from zds.tutorialv2.views.help import ChangeHelp
from zds.tutorialv2.views.labels import EditLabels
from zds.tutorialv2.views.suggestions import AddSuggestionView, RemoveSuggestionView
from zds.tutorialv2.views.tags import EditTags
from zds.tutorialv2.views.thumbnail import EditThumbnailView
from zds.tutorialv2.views.validations_contents import (
    AcceptValidation,
    ActivateJSFiddleInContent,
    AskValidationForContent,
    CancelValidation,
    RejectValidation,
    ReserveValidation,
    RevokeValidation,
)
from zds.tutorialv2.views.validations_opinions import PublishOpinion, UnpublishOpinion

# Notes on addition/deletion/update of managed signals
#
# * Addition
#     1. Add a key in `types`.
#     2. Modify the template "events/description.part.html" so that it is displayed properly.
#     3. Add the appropriate receiver.
#
# * Deletion
#     1. Remove the key in `types` and the corresponding `@receiver`.
#        This will make it impossible to record new events coming from this signal.
#     2. Do not modify the template, so that older events in the database keep being displayed properly.
#
# * Update
#     If a type name was to be updated for some reason, two options are possible :
#       - cleaner: update the production database to replace the old name with the new and also update the template
#       - simpler: update the template so that it knows the new name as well as the old name.


# Map signals to event types
types = {
    signals.authors_management: "authors_management",
    signals.contributors_management: "contributors_management",
    signals.beta_management: "beta_management",
    signals.validation_management: "validation_management",
    signals.thumbnail_management: "thumbnail_management",
    signals.tags_management: "tags_management",
    signals.canonical_link_management: "canonical_link_management",
    signals.goals_management: "goals_management",
    signals.labels_management: "labels_management",
    signals.suggestions_management: "suggestions_management",
    signals.help_management: "help_management",
    signals.jsfiddle_management: "jsfiddle_management",
    signals.opinions_management: "opinions_management",
}


class Event(models.Model):
    class Meta:
        verbose_name = "Événement sur un contenu"
        verbose_name_plural = "Événements sur un contenu"

    # Base fields
    date = models.DateTimeField(auto_now_add=True)
    performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=100)
    content = models.ForeignKey(PublishableContent, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)

    # Field used by author events
    author = models.ForeignKey(User, related_name="event_author", on_delete=models.SET_NULL, null=True)

    # Field used by contributor events
    contributor = models.ForeignKey(User, related_name="event_contributor", on_delete=models.SET_NULL, null=True)

    # Field used by beta and validation events
    version = models.CharField(null=True, max_length=80)


# Event recorders


@receiver(signals.beta_management, sender=ManageBetaContent)
def record_event_beta_management(sender, performer, signal, content, version, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        version=version,
        action=action,
    ).save()


@receiver(signals.authors_management, sender=AddAuthorToContent)
@receiver(signals.authors_management, sender=RemoveAuthorFromContent)
def record_event_author_management(sender, performer, signal, content, author, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        author=author,
        action=action,
    ).save()


@receiver(signals.contributors_management, sender=AddContributorToContent)
@receiver(signals.contributors_management, sender=RemoveContributorFromContent)
def record_event_contributor_management(sender, performer, signal, content, contributor, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        contributor=contributor,
        action=action,
    ).save()


@receiver(signals.validation_management, sender=AskValidationForContent)
@receiver(signals.validation_management, sender=CancelValidation)
@receiver(signals.validation_management, sender=AcceptValidation)
@receiver(signals.validation_management, sender=RejectValidation)
@receiver(signals.validation_management, sender=RevokeValidation)
@receiver(signals.validation_management, sender=ReserveValidation)
def record_event_validation_management(sender, performer, signal, content, version, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        version=version,
        action=action,
    ).save()


@receiver(signals.thumbnail_management, sender=EditThumbnailView)
def record_event_thumbnail_management(sender, performer, signal, content, **_):
    Event.objects.create(
        performer=performer,
        type=types[signal],
        content=content,
    )


@receiver(signals.tags_management, sender=EditTags)
def record_event_tags_management(sender, performer, signal, content, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
    ).save()


@receiver(signals.canonical_link_management, sender=EditCanonicalLinkView)
def record_event_canonical_link_management(sender, performer, signal, content, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
    ).save()


@receiver(signals.suggestions_management, sender=AddSuggestionView)
@receiver(signals.suggestions_management, sender=RemoveSuggestionView)
def record_event_suggestion_management(sender, performer, signal, content, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        action=action,
    ).save()


@receiver(signals.goals_management, sender=EditGoals)
def record_event_goals_management(sender, performer, signal, content, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
    ).save()


@receiver(signals.labels_management, sender=EditLabels)
def record_event_labels_management(sender, performer, signal, content, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
    ).save()


@receiver(signals.help_management, sender=ChangeHelp)
def record_event_help_management(sender, performer, signal, content, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
    ).save()


@receiver(signals.jsfiddle_management, sender=ActivateJSFiddleInContent)
def record_event_jsfiddle_management(sender, performer, signal, content, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        action=action,
    ).save()


@receiver(signals.opinions_management, sender=PublishOpinion)
@receiver(signals.opinions_management, sender=UnpublishOpinion)
def record_event_opinion_publication_management(sender, performer, signal, content, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        action=action,
    ).save()
