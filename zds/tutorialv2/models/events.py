from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2 import signals
from zds.tutorialv2.views.authors import AddAuthorToContent, RemoveAuthorFromContent
from zds.tutorialv2.views.beta import ManageBetaContent
from zds.tutorialv2.views.contributors import AddContributorToContent, RemoveContributorFromContent
from zds.tutorialv2.views.editorialization import EditContentTags, AddSuggestion, RemoveSuggestion
from zds.tutorialv2.views.help import ChangeHelp
from zds.tutorialv2.views.validations_contents import (
    ReserveValidation,
    AskValidationForContent,
    CancelValidation,
    RejectValidation,
    AcceptValidation,
    RevokeValidation,
    ActivateJSFiddleInContent,
)
from zds.tutorialv2.views.validations_opinions import PublishOpinion, UnpublishOpinion

# Notes on addition/deletion/update of managed signals
#
# * Addition
#     1. Add a key in `types`.
#     2. Write the corresponding event descriptor function.
#     3. Map the type to a descriptor in `descriptors` and voilà !
#
# * Deletion
#     1. Remove the key in `types` and the corresponding `@receiver`.
#        This will make it impossible to record new events coming from this signal.
#     2. Keep the event descriptor function and the type-descriptor mapping, so that
#        events in database are displayed properly.
#
# * Update
#     1. If a type name was to be updated for some reason, all the records in the database should also be updated
#        to match this change. Otherwise, no match will be found for the descriptors and it will display generic
#        information.


# Map signals to event types
types = {
    signals.authors_management: "authors_management",
    signals.contributors_management: "contributors_management",
    signals.beta_management: "beta_management",
    signals.validation_management: "validation_management",
    signals.tags_management: "tags_management",
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

    @property
    def description(self):
        try:
            return descriptors[self.type.__str__()](self)
        except KeyError:
            return describe_generic(self)


# Event descriptors


def describe_generic(event):
    return _("{} a déclenché un événement inconnu.").format(event.performer)


def describe_authors_management(event):
    performer_href = reverse("member-detail", args=[event.performer.username])
    author_href = reverse("member-detail", args=[event.author.username])
    if event.action == "add":
        return _('<a href="{}">{}</a> a ajouté <a href="{}">{}</a> à la liste des auteurs.').format(
            performer_href,
            event.performer,
            author_href,
            event.author,
        )
    elif event.action == "remove":
        return _('<a href="{}">{}</a> a supprimé <a href="{}">{}</a> de la liste des auteurs.').format(
            performer_href,
            event.performer,
            author_href,
            event.author,
        )
    else:
        return describe_generic(event)


def describe_contributors_management(event):
    performer_href = reverse("member-detail", args=[event.performer.username])
    contributor_href = reverse("member-detail", args=[event.contributor.username])
    if event.action == "add":
        return _('<a href="{}">{}</a> a ajouté <a href="{}">{}</a> à la liste des contributeurs.').format(
            performer_href,
            event.performer,
            contributor_href,
            event.contributor,
        )
    elif event.action == "remove":
        return _('<a href="{}">{}</a> a supprimé <a href="{}">{}</a> de la liste des contributeurs.').format(
            performer_href,
            event.performer,
            contributor_href,
            event.contributor,
        )
    else:
        return describe_generic(event)


def describe_beta_management(event):
    if event.action == "activate":
        return _('<a href="{}">{}</a> a mis une <a href="{}">version du contenu</a> en bêta.').format(
            reverse("member-detail", args=[event.performer.username]),
            event.performer,
            reverse("content:view", args=[event.content.pk, event.content.slug]) + f"?version={event.version}",
        )
    elif event.action == "deactivate":
        return _('<a href="{}">{}</a> a désactivé la bêta.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    else:
        return describe_generic(event)


def describe_validation_management(event):
    if event.action == "request":
        return _('<a href="{}">{}</a> a demandé la validation d\'une <a href="{}">version du contenu</a>.').format(
            reverse("member-detail", args=[event.performer.username]),
            event.performer,
            reverse("content:view", args=[event.content.pk, event.content.slug]) + f"?version={event.version}",
        )
    elif event.action == "cancel":
        return _('<a href="{}">{}</a> a annulé la demande de validation du contenu.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "accept":
        return _('<a href="{}">{}</a> a accepté le contenu pour publication.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "reject":
        return _('<a href="{}">{}</a> a refusé le contenu pour publication.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "revoke":
        return _('<a href="{}">{}</a> a dépublié le contenu.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "reserve":
        return _('<a href="{}">{}</a> a réservé le contenu pour validation.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "unreserve":
        return _('<a href="{}">{}</a> a annulé la réservation du contenu pour validation.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    else:
        return describe_generic(event)


def describe_tags_management(event):
    return _('<a href="{}">{}</a> a modifié les tags du contenu.').format(
        reverse("member-detail", args=[event.performer.username]), event.performer
    )


def describe_suggestions_management(event):
    if event.action == "add":
        return _('<a href="{}">{}</a> a ajouté une suggestion de contenu.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "remove":
        return _('<a href="{}">{}</a> a supprimé une suggestion de contenu.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    else:
        return describe_generic(event)


def describe_help_management(event):
    return _('<a href="{}">{}</a> a modifié les demandes d\'aide.').format(
        reverse("member-detail", args=[event.performer.username]), event.performer
    )


def describe_jsfiddle_management(event):
    if event.action == "activate":
        return _('<a href="{}">{}</a> a activé JSFiddle.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "deactivate":
        return _('<a href="{}">{}</a> a désactivé JSFiddle.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    else:
        return describe_generic(event)


def describe_opinions_management(event):
    if event.action == "publish":
        return _('<a href="{}">{}</a> a publié le billet.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )
    elif event.action == "unpublish":
        return _('<a href="{}">{}</a> a dépublié le billet.').format(
            reverse("member-detail", args=[event.performer.username]), event.performer
        )


# Map event types to descriptors
descriptors = {
    "authors_management": describe_authors_management,
    "contributors_management": describe_contributors_management,
    "beta_management": describe_beta_management,
    "validation_management": describe_validation_management,
    "tags_management": describe_tags_management,
    "suggestions_management": describe_suggestions_management,
    "help_management": describe_help_management,
    "jsfiddle_management": describe_jsfiddle_management,
    "opinions_management": describe_opinions_management,
}


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
@receiver(signals.validation_management, sender=ReserveValidation)
def record_event_validation_management(sender, performer, signal, content, version, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        version=version,
        action=action,
    ).save()


@receiver(signals.tags_management, sender=EditContentTags)
def record_event_tags_management(sender, performer, signal, content, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
    ).save()


@receiver(signals.suggestions_management, sender=AddSuggestion)
@receiver(signals.suggestions_management, sender=RemoveSuggestion)
def record_event_suggestion_management(sender, performer, signal, content, action, **_):
    Event(
        performer=performer,
        type=types[signal],
        content=content,
        action=action,
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
